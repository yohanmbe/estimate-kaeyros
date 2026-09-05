from src.moteur.categories import resoudre_categories_attendues
from src.moteur.types import RegleQuantite

MODELE_MARIAGE = [
    RegleQuantite(categorie="salle", base="jour"),
    RegleQuantite(categorie="mobilier", base="invite"),
    RegleQuantite(categorie="restauration", base="invite"),
    RegleQuantite(categorie="sonorisation", base="forfait"),
]


def test_prestations_souhaitees_vide_garde_toutes_les_categories_du_modele():
    resultat = resoudre_categories_attendues(
        MODELE_MARIAGE, prestations_souhaitees=[], prestations_exclues=[]
    )

    assert {regle.categorie for regle in resultat} == {
        "salle",
        "mobilier",
        "restauration",
        "sonorisation",
    }


def test_categorie_exclue_est_retiree_du_modele():
    resultat = resoudre_categories_attendues(
        MODELE_MARIAGE, prestations_souhaitees=[], prestations_exclues=["sonorisation"]
    )

    assert "sonorisation" not in {regle.categorie for regle in resultat}


def test_prestations_souhaitees_limite_aux_categories_demandees():
    resultat = resoudre_categories_attendues(
        MODELE_MARIAGE,
        prestations_souhaitees=["salle", "restauration"],
        prestations_exclues=[],
    )

    assert {regle.categorie for regle in resultat} == {"salle", "restauration"}
