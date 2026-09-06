from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue
from src.orchestration.machine import decider_prochaine_etape
from src.orchestration.types import PassageChiffrage, QuestionBesoin, QuestionChoixRessources

BESOIN_COMPLET = Besoin(
    type_evenement="mariage",
    nombre_invites=300,
    duree_jours=2,
    ville="Yaounde",
    date_evenement="2026-07-12",
)


def ressource(id_: str, categorie: str) -> RessourceCatalogue:
    return RessourceCatalogue(
        id=id_,
        nom=id_,
        categorie=categorie,
        unite_facturation="forfait",
        prix_unitaire=100_000,
        attributs={},
    )


def test_besoin_vide_declenche_une_question_groupee_sur_tous_les_champs():
    decision = decider_prochaine_etape(Besoin())

    assert isinstance(decision, QuestionBesoin)
    assert decision.champs_manquants == (
        "type_evenement",
        "nombre_invites",
        "duree_jours",
        "ville",
        "date_evenement",
    )


def test_besoin_partiel_ne_redemande_pas_les_champs_deja_connus():
    besoin = Besoin(type_evenement="mariage", ville="Yaounde")

    decision = decider_prochaine_etape(besoin)

    assert isinstance(decision, QuestionBesoin)
    assert decision.champs_manquants == ("nombre_invites", "duree_jours", "date_evenement")


def test_besoin_complet_sans_categorie_a_choix_multiple_passe_au_chiffrage():
    decision = decider_prochaine_etape(BESOIN_COMPLET, candidats_par_categorie={})

    assert decision == PassageChiffrage()


def test_besoin_complet_sans_aucun_candidat_fourni_passe_au_chiffrage():
    decision = decider_prochaine_etape(BESOIN_COMPLET)

    assert decision == PassageChiffrage()


def test_besoin_complet_avec_categories_a_choix_multiple_les_demande_une_par_une():
    candidats_salle = [ressource("salle-1", "salle"), ressource("salle-2", "salle")]
    candidats = {
        "salle": candidats_salle,
        "restauration": [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")],
        "decoration": [ressource("deco-1", "decoration")],
    }

    decision = decider_prochaine_etape(BESOIN_COMPLET, candidats_par_categorie=candidats)

    assert decision == QuestionChoixRessources(categorie="salle", candidats=candidats_salle)


def test_choix_deja_faits_par_le_prospect_debloquent_le_passage_au_chiffrage():
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
    }
    besoin_avec_choix = Besoin(
        type_evenement=BESOIN_COMPLET.type_evenement,
        nombre_invites=BESOIN_COMPLET.nombre_invites,
        duree_jours=BESOIN_COMPLET.duree_jours,
        ville=BESOIN_COMPLET.ville,
        date_evenement=BESOIN_COMPLET.date_evenement,
        ressources_choisies=("salle-1",),
    )

    decision = decider_prochaine_etape(besoin_avec_choix, candidats_par_categorie=candidats)

    assert decision == PassageChiffrage()
