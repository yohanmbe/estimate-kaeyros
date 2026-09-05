import pytest

from src.moteur.quantites import calculer_quantite
from src.moteur.types import BesoinChiffrage, RegleQuantite

BESOIN = BesoinChiffrage(
    nombre_invites=300, duree_jours=2, quartier_souhaite="Bastos", budget_declare=None
)


def test_regle_par_invite_multiplie_par_nombre_invites():
    regle = RegleQuantite(categorie="mobilier", base="invite")

    assert calculer_quantite(regle, BESOIN) == 300


def test_regle_par_jour_multiplie_par_duree_jours():
    regle = RegleQuantite(categorie="salle", base="jour")

    assert calculer_quantite(regle, BESOIN) == 2


def test_regle_forfait_ignore_le_besoin():
    regle = RegleQuantite(categorie="decoration", base="forfait")

    assert calculer_quantite(regle, BESOIN) == 1


def test_regle_avec_multiplicateur_est_appliquee():
    regle = RegleQuantite(categorie="personnel", base="jour", multiplicateur=2)

    assert calculer_quantite(regle, BESOIN) == 4


def test_base_inconnue_leve_une_erreur():
    regle = RegleQuantite(categorie="salle", base="inconnue")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        calculer_quantite(regle, BESOIN)
