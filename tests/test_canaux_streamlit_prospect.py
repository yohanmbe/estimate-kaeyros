"""Écran Streamlit piloté sans navigateur (streamlit.testing), sans réseau ni Postgres"""
from html import unescape
from pathlib import Path

from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from src.db.models import (
    ETAT_COMPLETE,
    ETAT_EN_COURS,
    Demande,
    Devis,
    ModeleEvenement,
    Prospect,
    Ressource,
    Tenant,
)

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
SCENARIO_WEEKEND = "Ce weekend, samedi ou dimanche"
SCENARIO_CINQUANTE = "50 invités, salles trop grandes"

SAMEDI_LISIBLE = "samedi 12 septembre 2026"
DIMANCHE_LISIBLE = "dimanche 13 septembre 2026"

# L'écran sépare les milliers par des espaces insécables, écrits ici en clair
TOTAL_MARIAGE_300 = "3 300 000 FCFA"
TOTAL_MARIAGE_900_SANS_SALLE = "8 550 000 FCFA"
TOTAL_MARIAGE_300_SANS_SALLE = "2 850 000 FCFA"


def creer_tenant_etoile(session: Session, actif: bool = True) -> Tenant:
    """Installe une entreprise cliente avec son catalogue et son modèle Mariage"""
    tenant = Tenant(
        nom="Événements Étoile",
        slug="etoile",
        ville="Yaoundé",
        coordonnees="671234567, Bastos",
        actif=actif,
    )
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


def dernier_message_agent(ecran: AppTest) -> str:
    """La derniere phrase prononcee par l'agent, sans le reste du fil"""
    fil = texte_affiche(ecran)
    debut = fil.rfind('<span class="bulle__auteur">Estimate</span>')
    return fil[debut:].split("</div>")[0] if debut != -1 else ""


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


def passer_les_complements(ecran: AppTest) -> AppTest:
    """Franchit le dernier formulaire avant l'estimation, sans rien y écrire"""
    boutons = [bouton for bouton in ecran.button if bouton.key == "complements-soumettre"]
    return boutons[0].click().run() if boutons else ecran


def aller_jusqua_lestimation(ecran: AppTest) -> AppTest:
    """Déroule la fin du parcours : les choix restants, puis les compléments libres"""
    return passer_les_complements(choisir_premiere_option(ecran))


def demander_tout_en_sur_mesure(ecran: AppTest) -> AppTest:
    """Demande une proposition à l'entreprise tant qu'une catégorie en propose une"""
    while [bouton for bouton in ecran.button if bouton.label == "Demander"]:
        ecran = [bouton for bouton in ecran.button if bouton.label == "Demander"][0].click().run()
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

    ecran = aller_jusqua_lestimation(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))

    texte = texte_affiche(ecran)
    assert TOTAL_MARIAGE_300 in texte
    assert "non contractuelle" in texte


def test_estimation_affichee_propose_le_telechargement_du_pdf(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = aller_jusqua_lestimation(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))

    boutons_telechargement = ecran.download_button
    assert len(boutons_telechargement) == 1
    assert boutons_telechargement[0].label == "Télécharger le PDF"


def test_message_envoye_apres_avoir_choisi_une_salle_ne_perd_pas_ce_choix(base_branchee):
    """Le schéma JSON de l'extracteur n'inclut pas ressources_choisies : un
    message envoyé après un choix ne doit pas faire redemander ce choix."""
    creer_tenant_etoile(base_branchee)
    ecran = aller_jusqua_lestimation(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))
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
    ecran = aller_jusqua_lestimation(ecran)

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
    ecran = passer_les_complements(bouton_stop.click().run())

    texte = texte_affiche(ecran)
    assert "Choisissez votre restauration" not in texte
    assert "450\xa0000\xa0FCFA" in texte  # la salle choisie est bien chiffrée
    # Exclue par choix du prospect : elle sort du modèle, on ne la lui reproche pas
    assert "Non retenu" not in texte


def ouvrir_scenario_sans_salle(base_branchee) -> AppTest:
    """Amène l'écran à la question sur la salle, avec 900 invités et un catalogue plafonné à 500"""
    creer_tenant_etoile(base_branchee)
    ecran = demarrer_conversation("etoile")
    ecran = ecran.sidebar.selectbox[0].select(SCENARIO_SANS_SALLE).run()
    return repondre(ecran, ["Un mariage pour 900 invités", "Le 4 juillet 2026, sur deux jours"])


def test_aucune_salle_assez_grande_propose_les_plus_grandes_en_le_signalant(base_branchee):
    """Ne rien montrer laisserait croire que l'entreprise n'a aucune salle"""
    ecran = ouvrir_scenario_sans_salle(base_branchee)

    texte = texte_affiche(ecran)
    assert "Salle Mvan" in texte
    assert "500 places" in texte
    assert "la plus grande de notre catalogue" in texte
    assert "proposition sur mesure" in texte
    # Une seule salle proposée : la 300 n'a rien à faire là pour 900 invités
    assert "Salle Bastos" not in texte


def test_devis_sur_mesure_pour_la_salle_laisse_chiffrer_le_reste(base_branchee):
    ecran = ouvrir_scenario_sans_salle(base_branchee)

    bouton_sur_mesure = next(
        bouton for bouton in ecran.button if bouton.key == "sur-mesure-choix-salle"
    )
    ecran = aller_jusqua_lestimation(bouton_sur_mesure.click().run())

    assert TOTAL_MARIAGE_900_SANS_SALLE in texte_affiche(ecran)


def test_conversation_menee_jusquau_devis_laisse_une_demande_et_un_devis_en_base(base_branchee):
    """Sans cette écriture, la conversation ne laisserait aucune trace : ni
    relance commerciale possible, ni chiffre à afficher au gestionnaire.
    """
    creer_tenant_etoile(base_branchee)

    aller_jusqua_lestimation(repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300))

    demandes = base_branchee.query(Demande).all()
    devis = base_branchee.query(Devis).all()
    assert len(demandes) == 1
    assert demandes[0].etat == ETAT_COMPLETE
    assert demandes[0].canal == "streamlit"
    assert demandes[0].besoin["nombre_invites"] == 300
    assert len(devis) == 1
    assert devis[0].total == 3_300_000
    assert devis[0].demande_id == demandes[0].id


def test_interactions_apres_le_devis_nen_emettent_pas_un_second(base_branchee):
    """Streamlit rejoue le script à chaque interaction : le devis affiché doit
    rester le même document, pas une estimation réécrite à chaque clic (D11).
    """
    creer_tenant_etoile(base_branchee)
    ecran = aller_jusqua_lestimation(
        repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)
    )

    ecran = repondre(ecran, ["merci"])

    assert TOTAL_MARIAGE_300 in texte_affiche(ecran)
    assert len(base_branchee.query(Devis).all()) == 1


def test_conversation_abandonnee_avant_le_devis_laisse_une_demande_relancable(base_branchee):
    """Le commercial doit pouvoir rappeler un prospect qui n'est jamais allé au
    bout : la demande existe dès le début, avec ce qu'on sait déjà de lui.
    """
    creer_tenant_etoile(base_branchee)

    repondre(demarrer_conversation("etoile"), ["Je prépare un mariage"])

    demandes = base_branchee.query(Demande).all()
    assert len(demandes) == 1
    assert demandes[0].etat == ETAT_EN_COURS
    assert demandes[0].besoin["type_evenement"] == "mariage"
    assert demandes[0].prospect_id is not None
    assert base_branchee.query(Devis).all() == []


def test_impasse_sans_aucune_ligne_nenregistre_pas_une_estimation_a_zero(base_branchee):
    """Une impasse annoncée au prospect n'est pas un devis : l'enregistrer
    ferait entrer un total de zéro franc dans le montant moyen du tableau
    de bord.
    """
    tenant = creer_tenant_etoile(base_branchee)
    base_branchee.query(Ressource).filter(Ressource.tenant_id == tenant.id).delete()
    base_branchee.commit()

    # Catalogue vide : chaque catégorie ne propose plus qu'un devis sur mesure,
    # qu'il faut demander pour que la conversation atteigne l'estimation.
    ecran = passer_les_complements(
        demander_tout_en_sur_mesure(
            repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)
        )
    )

    texte = texte_affiche(ecran)
    assert "Aucune estimation possible en ligne" in texte
    # Le prospect repart avec de quoi joindre l'entreprise, pas dans le vide
    assert "671234567, Bastos" in texte
    assert base_branchee.query(Devis).all() == []
    assert base_branchee.query(Demande).one().etat == ETAT_EN_COURS


def test_changement_dentreprise_ouvre_une_demande_dans_le_bon_espace(base_branchee):
    """Le slug de l'URL peut changer sans que la session Streamlit change :
    la demande suivante doit appartenir au nouveau tenant, jamais à l'ancien.
    """
    etoile = creer_tenant_etoile(base_branchee)
    autre = Tenant(nom="Autre Entreprise", slug="autre", ville="Douala")
    base_branchee.add(autre)
    base_branchee.commit()
    ecran = repondre(demarrer_conversation("etoile"), ["Je prépare un mariage"])

    ecran.query_params["slug"] = "autre"
    soumettre_formulaire_prospect(ecran.run(), nom="Bea Kum", telephone="+237699999999")

    demandes = base_branchee.query(Demande).all()
    assert len(demandes) == 2
    assert {demande.tenant_id for demande in demandes} == {etoile.id, autre.id}
    demande_etoile = next(d for d in demandes if d.tenant_id == etoile.id)
    assert demande_etoile.besoin["type_evenement"] == "mariage"


def ouvrir_scenario_weekend(base_branchee) -> "AppTest":
    """Amène l'écran jusqu'à la question « samedi ou dimanche ? »"""
    creer_tenant_etoile(base_branchee)
    ecran = demarrer_conversation("etoile")
    ecran = ecran.sidebar.selectbox[0].select(SCENARIO_WEEKEND).run()
    return repondre(ecran, ["Un mariage ce weekend à Bastos, 300 personnes, une journée"])


def test_ce_weekend_fait_choisir_entre_samedi_et_dimanche(base_branchee):
    ecran = ouvrir_scenario_weekend(base_branchee)

    texte = texte_affiche(ecran)
    assert SAMEDI_LISIBLE in texte
    assert DIMANCHE_LISIBLE in texte
    libelles = [bouton.label for bouton in ecran.button]
    assert SAMEDI_LISIBLE in libelles
    assert DIMANCHE_LISIBLE in libelles


def test_aucun_montant_naffiche_tant_que_la_date_nest_pas_tranchee(base_branchee):
    ecran = ouvrir_scenario_weekend(base_branchee)

    assert "FCFA" not in texte_affiche(ecran)


def test_date_choisie_fait_avancer_la_conversation_vers_les_salles(base_branchee):
    ecran = ouvrir_scenario_weekend(base_branchee)

    bouton_samedi = next(b for b in ecran.button if b.label == SAMEDI_LISIBLE)
    ecran = bouton_samedi.click().run()

    texte = texte_affiche(ecran)
    assert "Choisissez votre salle" in texte
    assert DIMANCHE_LISIBLE not in [bouton.label for bouton in ecran.button]


def test_date_choisie_est_enregistree_dans_la_demande(base_branchee):
    """Changer de scénario rouvre une demande : c'est la dernière qui porte le choix"""
    ecran = ouvrir_scenario_weekend(base_branchee)

    next(b for b in ecran.button if b.label == SAMEDI_LISIBLE).click().run()

    besoins = [demande.besoin for demande in base_branchee.query(Demande).all()]
    assert any(
        besoin["date_evenement"] == "2026-09-12"
        and besoin["champs_confirmes"] == ["date_evenement"]
        and besoin["dates_possibles"] == []
        for besoin in besoins
    )


def test_message_de_choix_rappelle_invites_ville_et_duree(base_branchee):
    """Le prospect a décrit son événement plusieurs messages plus haut"""
    creer_tenant_etoile(base_branchee)

    ecran = repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)

    texte = texte_affiche(ecran)
    assert "300 invités" in texte
    assert "Yaoundé" in texte
    assert "1 jour(s)" in texte


def test_prestation_non_retenue_nest_pas_annoncee_comme_absente_du_catalogue(base_branchee):
    """La salle existait et convenait : dire le contraire trompe le prospect"""
    creer_tenant_etoile(base_branchee)
    ecran = repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)

    bouton_refus = next(bouton for bouton in ecran.button if bouton.key == "exclure-salle")
    ecran = choisir_premiere_option(bouton_refus.click().run())

    texte = texte_affiche(ecran)
    assert "Aucune salle du catalogue ne peut accueillir" not in texte


def test_devis_sur_mesure_affiche_les_coordonnees_de_lentreprise(base_branchee):
    ecran = ouvrir_scenario_sans_salle(base_branchee)

    bouton_sur_mesure = next(
        bouton for bouton in ecran.button if bouton.key == "sur-mesure-choix-salle"
    )
    ecran = aller_jusqua_lestimation(bouton_sur_mesure.click().run())

    texte = texte_affiche(ecran)
    assert "Proposition sur mesure" in texte
    assert "671234567, Bastos" in texte


def remplir_les_complements(ecran: AppTest, besoins: str, mot: str) -> AppTest:
    """Écrit dans le dernier formulaire avant l'estimation, puis le valide"""
    champ_besoins = next(c for c in ecran.text_area if c.key == "complements-besoins")
    champ_mot = next(c for c in ecran.text_area if c.key == "complements-commentaire")
    champ_besoins.set_value(besoins)
    champ_mot.set_value(mot)
    bouton = next(b for b in ecran.button if b.key == "complements-soumettre")
    return bouton.click().run()


def test_complements_sont_demandes_avant_tout_montant(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = choisir_premiere_option(
        repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)
    )

    assert "FCFA" not in texte_affiche(ecran)
    assert [b for b in ecran.button if b.key == "complements-soumettre"]


def test_complements_saisis_sont_enregistres_sur_la_demande(base_branchee):
    creer_tenant_etoile(base_branchee)
    ecran = choisir_premiere_option(
        repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)
    )

    ecran = remplir_les_complements(
        ecran, "Un feu d'artifice", "Merci de me rappeler le matin"
    )

    demande = base_branchee.query(Demande).one()
    assert demande.besoins_hors_catalogue == "Un feu d'artifice"
    assert demande.commentaire == "Merci de me rappeler le matin"
    assert TOTAL_MARIAGE_300 in texte_affiche(ecran)


def test_complements_laisses_vides_ne_bloquent_pas_lestimation(base_branchee):
    creer_tenant_etoile(base_branchee)

    ecran = aller_jusqua_lestimation(
        repondre(demarrer_conversation("etoile"), MESSAGES_MARIAGE_300)
    )

    demande = base_branchee.query(Demande).one()
    assert demande.besoins_hors_catalogue is None
    assert demande.commentaire is None
    assert TOTAL_MARIAGE_300 in texte_affiche(ecran)


def test_corriger_la_date_ne_redemande_que_la_date(base_branchee):
    """Le prospect qui dit « ce n'est pas la date » ne doit pas se voir demander autre chose"""
    ecran = ouvrir_scenario_weekend(base_branchee)

    bouton_corriger = next(
        bouton for bouton in ecran.button if bouton.key == "corriger-date_evenement"
    )
    ecran = bouton_corriger.click().run()

    question = dernier_message_agent(ecran)
    assert "la date" in question
    assert "le nombre d'invités" not in question
    assert "le type d'événement" not in question


def test_bouton_darret_apparait_apres_une_demande_sur_mesure(base_branchee):
    """Il avait disparu : seul un choix de ressource le faisait apparaître"""
    ecran = ouvrir_scenario_sans_salle(base_branchee)
    assert "J'ai tout ce qu'il me faut" not in [bouton.label for bouton in ecran.button]

    bouton_sur_mesure = next(
        bouton for bouton in ecran.button if bouton.key == "sur-mesure-choix-salle"
    )
    ecran = bouton_sur_mesure.click().run()

    assert "J'ai tout ce qu'il me faut" in [bouton.label for bouton in ecran.button]


def test_cinquante_invites_ne_voient_quune_salle_et_le_sur_mesure(base_branchee):
    """Le cas du premier test réel, de bout en bout à l'écran"""
    creer_tenant_etoile(base_branchee)
    ecran = demarrer_conversation("etoile")
    ecran = ecran.sidebar.selectbox[0].select(SCENARIO_CINQUANTE).run()
    ecran = repondre(ecran, ["Un mariage pour 50 invités le 12 décembre 2026, une journée"])

    texte = texte_affiche(ecran)
    assert "Salle Bastos" in texte
    assert "la plus petite de notre catalogue" in texte
    assert "Salle Mvan" not in texte
    assert "proposition sur mesure" in texte
