"""Parcours complet sans canal ni réseau : extraction simulée, décision, chiffrage"""
from dataclasses import replace

from src.extraction.mock import ExtracteurMock
from src.extraction.types import Besoin
from src.moteur.types import RegleQuantite, RessourceCatalogue
from src.orchestration.machine import decider_prochaine_etape
from src.orchestration.parcours import chiffrer_pour_besoin, resoudre_candidats
from src.orchestration.types import (
    PassageChiffrage,
    QuestionBesoin,
    QuestionChoixRessources,
    QuestionComplements,
)

CATALOGUE = [
    RessourceCatalogue(
        id="salle-bastos",
        nom="Salle Bastos",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=450_000,
        attributs={"capacite": 300, "quartier": "Bastos"},
    ),
    RessourceCatalogue(
        id="salle-mvan",
        nom="Salle Mvan",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=600_000,
        attributs={"capacite": 500, "quartier": "Mvan"},
    ),
    RessourceCatalogue(
        id="salle-odza",
        nom="Salle Odza",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=250_000,
        attributs={"capacite": 150, "quartier": "Odza"},
    ),
    RessourceCatalogue(
        id="chaise",
        nom="Chaise Napoléon",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=1_500,
        attributs={},
    ),
    RessourceCatalogue(
        id="menu",
        nom="Menu Standard",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=8_000,
        attributs={},
    ),
]

MODELE_MARIAGE = [
    RegleQuantite(categorie="salle", base="jour", multiplicateur=1),
    RegleQuantite(categorie="mobilier", base="invite", multiplicateur=1),
    RegleQuantite(categorie="restauration", base="invite", multiplicateur=1),
]

BESOIN_MARIAGE_300 = Besoin(
    type_evenement="mariage",
    date_evenement="2026-12-12",
    ville="Yaoundé",
    quartier_souhaite="Bastos",
    nombre_invites=300,
    duree_jours=1,
)


def decider(besoin: Besoin, complements_fournis: bool = False):
    """Reproduit l'enchaînement que le canal applique à chaque tour"""
    return decider_prochaine_etape(
        besoin,
        resoudre_candidats(besoin, CATALOGUE, MODELE_MARIAGE),
        complements_fournis,
    )


def test_besoin_incomplet_ne_declenche_aucune_selection_de_ressource():
    besoin = Besoin(type_evenement="mariage", nombre_invites=300)

    assert resoudre_candidats(besoin, CATALOGUE, MODELE_MARIAGE) == {}


def test_besoin_incomplet_fait_poser_une_question_groupee():
    decision = decider(Besoin(type_evenement="mariage"))

    assert isinstance(decision, QuestionBesoin)
    assert decision.champs_manquants == ("nombre_invites", "duree_jours", "ville", "date_evenement")


def test_mariage_300_invites_bastos_propose_la_salle_du_quartier_en_premier():
    decision = decider(BESOIN_MARIAGE_300)

    assert isinstance(decision, QuestionChoixRessources)
    assert decision.categorie == "salle"
    assert [candidat.nom for candidat in decision.candidats] == ["Salle Bastos", "Salle Mvan"]


def test_salle_seule_choisie_ne_suffit_pas_encore_au_chiffrage():
    """Mobilier et restauration n'ont qu'un candidat chacun, mais restent à
    trancher : rien n'entre au devis sans un choix explicite du prospect."""
    besoin = replace(BESOIN_MARIAGE_300, ressources_choisies=("salle-bastos",))

    decision = decider(besoin)

    assert isinstance(decision, QuestionChoixRessources)
    assert decision.categorie == "mobilier"


def test_tous_les_choix_faits_menent_au_dernier_mot_du_prospect():
    """Avant l'estimation, il reste une occasion de signaler ce qui manque au catalogue"""
    besoin = replace(
        BESOIN_MARIAGE_300, ressources_choisies=("salle-bastos", "chaise", "menu")
    )

    assert isinstance(decider(besoin), QuestionComplements)


def test_complements_fournis_font_passer_la_conversation_au_chiffrage():
    besoin = replace(
        BESOIN_MARIAGE_300, ressources_choisies=("salle-bastos", "chaise", "menu")
    )

    assert isinstance(decider(besoin, complements_fournis=True), PassageChiffrage)


def test_mariage_300_invites_bastos_calcule_total_correct():
    besoin = replace(
        BESOIN_MARIAGE_300, ressources_choisies=("salle-bastos", "chaise", "menu")
    )

    resultat = chiffrer_pour_besoin(besoin, CATALOGUE, MODELE_MARIAGE)

    assert [(ligne.designation, ligne.quantite, ligne.montant) for ligne in resultat.lignes] == [
        ("Salle Bastos", 1, 450_000),
        ("Chaise Napoléon", 300, 450_000),
        ("Menu Standard", 300, 2_400_000),
    ]
    assert resultat.total == 3_300_000


def test_mariage_900_invites_signale_la_salle_comme_non_satisfaite():
    besoin = replace(
        BESOIN_MARIAGE_300,
        nombre_invites=900,
        duree_jours=2,
        ressources_choisies=("chaise", "menu"),
    )

    resultat = chiffrer_pour_besoin(besoin, CATALOGUE, MODELE_MARIAGE)

    assert [categorie.categorie for categorie in resultat.categories_non_satisfaites] == ["salle"]
    assert [ligne.designation for ligne in resultat.lignes] == ["Chaise Napoléon", "Menu Standard"]
    assert resultat.total == 8_550_000


def test_budget_declare_depasse_est_signale_sans_modifier_le_total():
    besoin = replace(
        BESOIN_MARIAGE_300,
        ressources_choisies=("salle-bastos", "chaise", "menu"),
        budget_declare=2_000_000,
    )

    resultat = chiffrer_pour_besoin(besoin, CATALOGUE, MODELE_MARIAGE)

    assert resultat.depasse_budget is True
    assert resultat.total == 3_300_000


def test_conversation_de_trois_messages_mene_de_la_question_au_choix_de_salle():
    extracteur = ExtracteurMock(
        besoins_a_renvoyer=[
            Besoin(type_evenement="mariage"),
            replace(BESOIN_MARIAGE_300, date_evenement=None, duree_jours=None),
            BESOIN_MARIAGE_300,
        ]
    )
    messages = [
        "Je prépare un mariage",
        "300 invités à Yaoundé, de préférence à Bastos",
        "Le 12 décembre 2026, sur une seule journée",
    ]

    besoin = Besoin()
    decisions = []
    for message in messages:
        besoin = extracteur.extraire_besoin(message, besoin)
        decisions.append(decider(besoin))

    assert isinstance(decisions[0], QuestionBesoin)
    assert isinstance(decisions[1], QuestionBesoin)
    assert isinstance(decisions[2], QuestionChoixRessources)
    assert extracteur.messages_recus == messages
