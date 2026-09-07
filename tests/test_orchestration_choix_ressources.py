from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue
from src.orchestration.choix_ressources import (
    identifier_categories_restant_a_choisir,
    identifier_prochaine_categorie_a_choisir,
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


def test_categorie_a_un_seul_candidat_n_est_jamais_a_choisir():
    candidats = {"decoration": [ressource("deco-1", "decoration")]}

    resultat = identifier_prochaine_categorie_a_choisir(Besoin(), candidats)

    assert resultat is None


def test_categorie_a_plusieurs_candidats_sans_choix_du_prospect_est_a_choisir():
    candidats_salle = [ressource("salle-1", "salle"), ressource("salle-2", "salle")]

    resultat = identifier_prochaine_categorie_a_choisir(Besoin(), {"salle": candidats_salle})

    assert resultat == ("salle", candidats_salle)


def test_categorie_deja_choisie_par_le_prospect_n_est_plus_a_choisir():
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
    }
    besoin = Besoin(ressources_choisies=("salle-1",))

    resultat = identifier_prochaine_categorie_a_choisir(besoin, candidats)

    assert resultat is None


def test_plusieurs_categories_a_choix_multiple_ne_sont_jamais_groupees():
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
        "restauration": [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")],
    }

    resultat = identifier_prochaine_categorie_a_choisir(Besoin(), candidats)

    assert resultat is not None
    categorie, _ = resultat
    assert categorie in {"salle", "restauration"}


def test_categorie_resolue_laisse_place_a_la_suivante():
    candidats_restauration = [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")]
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
        "restauration": candidats_restauration,
    }
    besoin = Besoin(ressources_choisies=("salle-1",))

    resultat = identifier_prochaine_categorie_a_choisir(besoin, candidats)

    assert resultat == ("restauration", candidats_restauration)


def test_aucune_categorie_ne_correspond_quand_toutes_sont_resolues():
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
        "restauration": [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")],
    }
    besoin = Besoin(ressources_choisies=("salle-1", "resto-2"))

    resultat = identifier_prochaine_categorie_a_choisir(besoin, candidats)

    assert resultat is None


def test_categories_restant_a_choisir_renvoie_tout_pas_seulement_la_premiere():
    """Sert au bouton « j'ai tout ce qu'il me faut » : il faut pouvoir exclure
    toutes les catégories en attente d'un coup, pas une par une."""
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
        "mobilier": [ressource("chaise-1", "mobilier")],
        "restauration": [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")],
        "decoration": [ressource("deco-1", "decoration"), ressource("deco-2", "decoration")],
    }

    resultat = identifier_categories_restant_a_choisir(Besoin(), candidats)

    assert resultat == ["salle", "restauration", "decoration"]


def test_categories_deja_choisies_ou_a_candidat_unique_absentes_du_reste_a_choisir():
    candidats = {
        "salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")],
        "mobilier": [ressource("chaise-1", "mobilier")],
        "restauration": [ressource("resto-1", "restauration"), ressource("resto-2", "restauration")],
    }
    besoin = Besoin(ressources_choisies=("resto-1",))

    resultat = identifier_categories_restant_a_choisir(besoin, candidats)

    assert resultat == ["salle"]


def test_aucune_categorie_restante_quand_tout_est_decide():
    candidats = {"salle": [ressource("salle-1", "salle"), ressource("salle-2", "salle")]}
    besoin = Besoin(ressources_choisies=("salle-1",))

    assert identifier_categories_restant_a_choisir(besoin, candidats) == []
