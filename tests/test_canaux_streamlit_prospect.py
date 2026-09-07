"""Écran Streamlit piloté sans navigateur (streamlit.testing), sans réseau ni Postgres"""
from html import unescape
from pathlib import Path

from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from src.db.models import ModeleEvenement, Ressource, Tenant

CHEMIN_ECRAN = str(
    Path(__file__).resolve().parents[1] / "src" / "canaux" / "streamlit_prospect.py"
)

RESSOURCES_DE_TEST = [
    ("Salle Bastos", "salle", "jour", 450_000, {"capacite": 300, "quartier": "Bastos"}),
    ("Salle Mvan", "salle", "jour", 600_000, {"capacite": 500, "quartier": "Mvan"}),
    ("Chaise Napoléon", "mobilier", "unite", 1_500, {}),
    ("Menu Standard", "restauration", "personne", 8_000, {}),
]

MODELE_DE_TEST = [
    {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1},
    {"categorie": "mobilier", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
    {"categorie": "restauration", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
]

MESSAGES_MARIAGE_300 = [
    "Je prépare un mariage",
    "300 invités à Yaoundé, de préférence à Bastos",
    "Le 12 décembre 2026, sur une seule journée",
]

SCENARIO_SANS_SALLE = "900 invités, salle insuffisante"

# L'écran sépare les milliers par des espaces insécables, écrits ici en clair
TOTAL_MARIAGE_300 = "3 300 000 FCFA"
TOTAL_MARIAGE_900_SANS_SALLE = "8 550 000 FCFA"
TOTAL_MARIAGE_300_SANS_SALLE = "2 850 000 FCFA"


def creer_tenant_etoile(session: Session, actif: bool = True) -> Tenant:
    """Installe une entreprise cliente avec son catalogue et son modèle Mariage"""
    tenant = Tenant(nom="Événements Étoile", slug="etoile", ville="Yaoundé", actif=actif)
    session.add(tenant)
    session.flush()
    session.add_all(
        Ressource(
            tenant_id=tenant.id,
            nom=nom,
            categorie=categorie,
            unite_facturation=unite,
            prix_unitaire=prix,
            attributs=attributs,
        )
        for nom, categorie, unite, prix, attributs in RESSOURCES_DE_TEST
    )
    session.add(
        ModeleEvenement(tenant_id=tenant.id, nom="Mariage", lignes_par_defaut=MODELE_DE_TEST)
    )
    session.commit()
    return tenant


def lancer_ecran(slug: str | None = None) -> AppTest:
    """Exécute l'écran comme le ferait un navigateur, avec le slug dans l'URL"""
    ecran = AppTest.from_file(CHEMIN_ECRAN, default_timeout=30)
    if slug is not None:
        ecran.query_params["slug"] = slug
    return ecran.run()


def texte_affiche(ecran: AppTest) -> str:
    """Tout le texte rendu par l'écran, pour y chercher un montant ou un message.

    Les entités HTML sont retraduites : un test porte sur ce que le prospect
    lit, pas sur la façon dont le balisage échappe les apostrophes.
    """
    return unescape("\n".join(element.value for element in ecran.markdown))


def repondre(ecran: AppTest, messages: list[str]) -> AppTest:
    """Envoie les messages du prospect l'un après l'autre"""
    for message in messages:
        ecran = ecran.chat_input[0].set_value(message).run()
    return ecran


def choisir_premiere_option(ecran: AppTest) -> AppTest:
    """Retient la première ressource proposée, tant qu'un choix est demandé"""
    while [bouton for bouton in ecran.button if bouton.label == "Choisir"]:
        ecran = [bouton for bouton in ecran.button if bouton.label == "Choisir"][0].click().run()
    return ecran


def test_lien_sans_slug_naffiche_aucun_chat(base_branchee):
    ecran = lancer_ecran()

    assert "Ce lien ne précise pas l'entreprise" in texte_affiche(ecran)
    assert ecran.chat_input == []


def test_slug_inconnu_naffiche_aucun_chat(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = lancer_ecran("entreprise-inexistante")

    assert "Ce lien ne correspond à aucune entreprise" in texte_affiche(ecran)
    assert ecran.chat_input == []


def test_tenant_desactive_naffiche_aucun_chat(base_branchee):
    creer_tenant_etoile(base_branchee, actif=False)

    ecran = lancer_ecran("etoile")

    assert "Cet espace d'estimation est fermé" in texte_affiche(ecran)
    assert ecran.chat_input == []


def test_ecran_accueille_le_prospect_au_nom_de_lentreprise(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = lancer_ecran("etoile")

    assert "Événements Étoile" in texte_affiche(ecran)
    assert ecran.chat_input != []


def test_besoin_incomplet_fait_poser_une_question_avant_tout_montant(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(lancer_ecran("etoile"), ["Je prépare un mariage"])

    texte = texte_affiche(ecran)
    assert "Il me manque" in texte
    assert "FCFA" not in texte


def test_salle_hors_du_quartier_souhaite_reste_proposee(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300)

    texte = texte_affiche(ecran)
    assert "Salle Bastos" in texte
    assert "Salle Mvan" in texte


def test_mariage_300_invites_bastos_affiche_le_total_de_lestimation(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = choisir_premiere_option(repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300))

    texte = texte_affiche(ecran)
    assert TOTAL_MARIAGE_300 in texte
    assert "non contractuelle" in texte


def test_estimation_affichee_propose_le_telechargement_du_pdf(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = choisir_premiere_option(repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300))

    boutons_telechargement = ecran.download_button
    assert len(boutons_telechargement) == 1
    assert boutons_telechargement[0].label == "Télécharger le PDF"


def test_message_envoye_apres_avoir_choisi_une_salle_ne_perd_pas_ce_choix(base_branchee):
    """Le schéma JSON de l'extracteur n'inclut pas ressources_choisies : un
    message envoyé après un choix ne doit pas faire redemander ce choix."""
    creer_tenant_etoile(base_branchee)
    ecran = choisir_premiere_option(repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300))
    assert TOTAL_MARIAGE_300 in texte_affiche(ecran)

    ecran = repondre(ecran, ["merci"])

    texte = texte_affiche(ecran)
    assert TOTAL_MARIAGE_300 in texte
    assert "Choisissez votre salle" not in texte


def test_recapitulatif_besoin_reflete_les_informations_connues(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300)

    texte = texte_affiche(ecran)
    assert "Votre événement" in texte
    assert "300" in texte
    assert "Bastos" in texte


def test_fournisseur_reel_affiche_le_recapitulatif_sans_nommer_le_fournisseur(
    base_branchee, monkeypatch
):
    creer_tenant_etoile(base_branchee)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "cle-de-test")

    texte = texte_affiche(lancer_ecran("etoile"))

    assert "Votre événement" in texte
    assert "groq" not in texte.lower()
    assert "à préciser" in texte


def test_prospect_peut_refuser_une_categorie_plutot_que_choisir(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = repondre(lancer_ecran("etoile"), MESSAGES_MARIAGE_300)

    bouton_refus = next(bouton for bouton in ecran.button if bouton.key == "exclure-salle")
    ecran = bouton_refus.click().run()

    texte = texte_affiche(ecran)
    assert "Salle Bastos" not in texte
    assert "Salle Mvan" not in texte
    assert "Chaise Napoléon" in texte
    assert TOTAL_MARIAGE_300_SANS_SALLE in texte
    assert "Non chiffré" not in texte


def test_aucune_salle_assez_grande_est_annoncee_sans_bloquer_le_reste(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = lancer_ecran("etoile")

    ecran = ecran.sidebar.selectbox[0].select(SCENARIO_SANS_SALLE).run()
    ecran = repondre(ecran, ["Un mariage pour 900 invités", "Le 4 juillet 2026, sur deux jours"])

    texte = texte_affiche(ecran)
    assert "Aucune salle du catalogue ne peut accueillir 900 invités." in texte
    assert TOTAL_MARIAGE_900_SANS_SALLE in texte
