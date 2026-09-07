"""Écran Streamlit piloté sans navigateur (streamlit.testing), sans réseau ni Postgres"""
from html import unescape
from pathlib import Path

from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from src.db.models import ModeleEvenement, Prospect, Ressource, Tenant

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


def soumettre_formulaire_prospect(
    ecran: AppTest, nom: str = "Awa Ngo", telephone: str = "+237690000000"
) -> AppTest:
    """Remplit et valide le formulaire d'identification affiché avant le chat"""
    champ_nom = next(c for c in ecran.text_input if c.key == "prospect-nom")
    champ_telephone = next(c for c in ecran.text_input if c.key == "prospect-telephone")
    champ_nom.set_value(nom)
    champ_telephone.set_value(telephone)
    bouton_soumettre = next(b for b in ecran.button if b.key == "prospect-soumettre")
    return bouton_soumettre.click().run()


def demarrer_conversation(slug: str) -> AppTest:
    """Charge l'écran et franchit le formulaire d'identification, jusqu'au chat"""
    return soumettre_formulaire_prospect(lancer_ecran(slug))


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

    ecran = demarrer_conversation("etoile")

    assert "Événements Étoile" in texte_affiche(ecran)
    assert ecran.chat_input != []


def test_message_daccueil_personnalise_avec_le_nom_du_prospect(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = soumettre_formulaire_prospect(lancer_ecran("etoile"), nom="Awa Ngo")

    assert "Bonjour Awa Ngo" in texte_affiche(ecran)


def test_formulaire_prospect_avec_telephone_invalide_affiche_une_erreur(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = soumettre_formulaire_prospect(lancer_ecran("etoile"), telephone="pas-un-numero")

    assert "numéro de téléphone" in ecran.error[0].value
    assert ecran.chat_input == []


def test_formulaire_prospect_avec_email_invalide_affiche_une_erreur(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = lancer_ecran("etoile")

    champ_nom = next(c for c in ecran.text_input if c.key == "prospect-nom")
    champ_telephone = next(c for c in ecran.text_input if c.key == "prospect-telephone")
    champ_email = next(c for c in ecran.text_input if c.key == "prospect-email")
    champ_nom.set_value("Awa Ngo")
    champ_telephone.set_value("+237690000000")
    champ_email.set_value("pas-un-email")
    bouton_soumettre = next(b for b in ecran.button if b.key == "prospect-soumettre")
    ecran = bouton_soumettre.click().run()

    assert "adresse email" in ecran.error[0].value
    assert ecran.chat_input == []


def test_formulaire_prospect_bloque_le_chat_tant_quil_nest_pas_soumis(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = lancer_ecran("etoile")

    assert "Événements Étoile" in texte_affiche(ecran)
    assert ecran.chat_input == []


def test_formulaire_prospect_sans_nom_ni_telephone_affiche_une_erreur(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = lancer_ecran("etoile")

    bouton_soumettre = next(b for b in ecran.button if b.key == "prospect-soumettre")
    ecran = bouton_soumettre.click().run()

    assert "Merci d'indiquer votre nom et votre téléphone" in ecran.error[0].value
    assert ecran.chat_input == []


def test_formulaire_prospect_valide_cree_une_ligne_prospect_en_base(base_branchee):
    creer_tenant_etoile(base_branchee)

    demarrer_conversation("etoile")

    prospects = base_branchee.query(Prospect).all()
    assert len(prospects) == 1
    assert prospects[0].nom == "Awa Ngo"
    assert prospects[0].telephone == "+237690000000"
    assert prospects[0].consentement_contact is True


def test_changement_de_tenant_redemande_le_formulaire_prospect(base_branchee):
    creer_tenant_etoile(base_branchee)
    base_branchee.add(Tenant(nom="Autre Entreprise", slug="autre", ville="Douala"))
    base_branchee.commit()

    ecran = demarrer_conversation("etoile")
    assert ecran.chat_input != []

    ecran.query_params["slug"] = "autre"
    ecran = ecran.run()

    assert "Autre Entreprise" in texte_affiche(ecran)
    assert ecran.chat_input == []


def test_besoin_incomplet_fait_poser_une_question_avant_tout_montant(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(demarrer_conversation("etoile"), ["Je prépare un mariage"])

    texte = texte_affiche(ecran)
    assert "Il me manque" in texte
    assert "FCFA" not in texte


def test_salle_hors_du_quartier_souhaite_reste_proposee(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)

    texte = texte_affiche(ecran)
    assert "Salle Bastos" in texte
    assert "Salle Mvan" in texte


def test_mariage_300_invites_bastos_affiche_le_total_de_lestimation(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = choisir_premiere_option(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))

    texte = texte_affiche(ecran)
    assert TOTAL_MARIAGE_300 in texte
    assert "non contractuelle" in texte


def test_estimation_affichee_propose_le_telechargement_du_pdf(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = choisir_premiere_option(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))

    boutons_telechargement = ecran.download_button
    assert len(boutons_telechargement) == 1
    assert boutons_telechargement[0].label == "Télécharger le PDF"


def test_message_envoye_apres_avoir_choisi_une_salle_ne_perd_pas_ce_choix(base_branchee):
    """Le schéma JSON de l'extracteur n'inclut pas ressources_choisies : un
    message envoyé après un choix ne doit pas faire redemander ce choix."""
    creer_tenant_etoile(base_branchee)
    ecran = choisir_premiere_option(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))
    assert TOTAL_MARIAGE_300 in texte_affiche(ecran)

    ecran = repondre(ecran, ["merci"])

    texte = texte_affiche(ecran)
    assert TOTAL_MARIAGE_300 in texte
    assert "Choisissez votre salle" not in texte


def test_recapitulatif_besoin_reflete_les_informations_connues(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)

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

    texte = texte_affiche(demarrer_conversation("etoile"))

    assert "Votre événement" in texte
    assert "groq" not in texte.lower()
    assert "à préciser" in texte


def test_prospect_peut_refuser_une_categorie_plutot_que_choisir(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)

    bouton_refus = next(bouton for bouton in ecran.button if bouton.key == "exclure-salle")
    ecran = bouton_refus.click().run()
    # Mobilier et restauration n'ont qu'un candidat chacun, mais restent à
    # trancher (rien n'entre au devis sans un choix explicite).
    ecran = choisir_premiere_option(ecran)

    texte = texte_affiche(ecran)
    assert "Salle Bastos" not in texte
    assert "Salle Mvan" not in texte
    assert "Chaise Napoléon" in texte
    assert TOTAL_MARIAGE_300_SANS_SALLE in texte
    assert "Non chiffré" not in texte


def creer_tenant_avec_deux_categories_a_choix_multiple(session: Session) -> Tenant:
    """Salle et restauration ont chacune deux candidats, contrairement à
    creer_tenant_etoile où seule la salle en a plusieurs : nécessaire pour
    tester l'arrêt du parcours de choix avant la fin du catalogue."""
    tenant = Tenant(nom="Événements Deux Choix", slug="deux-choix", ville="Yaoundé")
    session.add(tenant)
    session.flush()
    session.add_all(
        Ressource(
            tenant_id=tenant.id, nom=nom, categorie=categorie, unite_facturation=unite,
            prix_unitaire=prix, attributs=attributs,
        )
        for nom, categorie, unite, prix, attributs in [
            ("Salle Bastos", "salle", "jour", 450_000, {"capacite": 300, "quartier": "Bastos"}),
            ("Salle Mvan", "salle", "jour", 600_000, {"capacite": 500, "quartier": "Mvan"}),
            ("Menu Standard", "restauration", "personne", 8_000, {}),
            ("Menu Prestige", "restauration", "personne", 15_000, {}),
        ]
    )
    session.add(
        ModeleEvenement(
            tenant_id=tenant.id, nom="Mariage",
            lignes_par_defaut=[
                {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1},
                {"categorie": "restauration", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
            ],
        )
    )
    session.commit()
    return tenant


def test_bouton_jai_tout_ce_quil_me_faut_absent_avant_tout_choix(base_branchee):
    """Sans ça, un prospect pourrait tout arrêter avant d'avoir rien choisi,
    et l'estimation contiendrait quand même les catégories à candidat unique
    (ex. la logistique) qu'il n'a jamais validées lui-même."""
    creer_tenant_avec_deux_categories_a_choix_multiple(base_branchee)

    ecran = repondre(demarrer_conversation("deux-choix"), MESSAGES_MARIAGE_300)

    labels = [bouton.label for bouton in ecran.button]
    assert "Je ne veux pas de salle" in labels
    assert "J'ai tout ce qu'il me faut" not in labels


def test_bouton_jai_tout_ce_quil_me_faut_apparait_apres_un_premier_choix(base_branchee):
    creer_tenant_avec_deux_categories_a_choix_multiple(base_branchee)
    ecran = repondre(demarrer_conversation("deux-choix"), MESSAGES_MARIAGE_300)

    ecran = [bouton for bouton in ecran.button if bouton.label == "Choisir"][0].click().run()

    labels = [bouton.label for bouton in ecran.button]
    assert "J'ai tout ce qu'il me faut" in labels


def test_bouton_jai_tout_ce_quil_me_faut_arrete_le_parcours_de_choix(base_branchee):
    creer_tenant_avec_deux_categories_a_choix_multiple(base_branchee)
    ecran = repondre(demarrer_conversation("deux-choix"), MESSAGES_MARIAGE_300)

    # Choisit la première salle, ce qui ferait normalement passer à la
    # question sur la restauration.
    ecran = [bouton for bouton in ecran.button if bouton.label == "Choisir"][0].click().run()
    assert "Choisissez votre restauration" in texte_affiche(ecran)

    bouton_stop = next(bouton for bouton in ecran.button if bouton.label == "J'ai tout ce qu'il me faut")
    ecran = bouton_stop.click().run()

    texte = texte_affiche(ecran)
    assert "Choisissez votre restauration" not in texte
    assert "450\xa0000\xa0FCFA" in texte  # la salle choisie est bien chiffrée
    assert "Non chiffré" not in texte  # exclue par choix, pas un trou du catalogue


def test_aucune_salle_assez_grande_est_annoncee_sans_bloquer_le_reste(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = demarrer_conversation("etoile")

    ecran = ecran.sidebar.selectbox[0].select(SCENARIO_SANS_SALLE).run()
    ecran = repondre(ecran, ["Un mariage pour 900 invités", "Le 4 juillet 2026, sur deux jours"])
    ecran = choisir_premiere_option(ecran)

    texte = texte_affiche(ecran)
    assert "Aucune salle du catalogue ne peut accueillir 900 invités." in texte
    assert TOTAL_MARIAGE_900_SANS_SALLE in texte
