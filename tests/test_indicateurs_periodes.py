from datetime import date, datetime

import pytest

from src.indicateurs.periodes import (
    LIBELLES_PERIODES,
    periode_de_lannee,
    periode_de_toujours,
    periode_depuis_libelle,
    periode_du_mois,
    periode_du_trimestre,
)

UN_JOUR_DE_FEVRIER = date(2026, 2, 17)


def test_ce_mois_va_du_premier_au_dernier_jour_du_mois():
    periode = periode_du_mois(UN_JOUR_DE_FEVRIER)

    assert periode.debut == datetime(2026, 2, 1)
    assert periode.fin == datetime(2026, 2, 28, 23, 59, 59, 999999)


def test_ce_mois_tient_compte_dune_annee_bissextile():
    periode = periode_du_mois(date(2028, 2, 3))

    assert periode.fin == datetime(2028, 2, 29, 23, 59, 59, 999999)


def test_ce_trimestre_englobe_les_trois_mois_du_trimestre_courant():
    periode = periode_du_trimestre(UN_JOUR_DE_FEVRIER)

    assert periode.debut == datetime(2026, 1, 1)
    assert periode.fin == datetime(2026, 3, 31, 23, 59, 59, 999999)


def test_un_jour_de_septembre_tombe_dans_le_trimestre_de_juillet_a_septembre():
    periode = periode_du_trimestre(date(2026, 9, 7))

    assert periode.debut == datetime(2026, 7, 1)
    assert periode.fin == datetime(2026, 9, 30, 23, 59, 59, 999999)


def test_un_jour_de_decembre_tombe_dans_le_dernier_trimestre():
    periode = periode_du_trimestre(date(2026, 12, 31))

    assert periode.debut == datetime(2026, 10, 1)
    assert periode.fin == datetime(2026, 12, 31, 23, 59, 59, 999999)


def test_cette_annee_va_du_premier_janvier_au_trente_et_un_decembre():
    periode = periode_de_lannee(UN_JOUR_DE_FEVRIER)

    assert periode.debut == datetime(2026, 1, 1)
    assert periode.fin == datetime(2026, 12, 31, 23, 59, 59, 999999)


def test_tout_ne_borne_pas_par_le_bas():
    """« Tout » (voir D48) doit couvrir l'historique complet d'un tenant,
    sans dépendre d'une vraie date de première demande.
    """
    periode = periode_de_toujours(UN_JOUR_DE_FEVRIER)

    assert periode.debut.year < 2024
    assert periode.fin == datetime(2026, 2, 17, 23, 59, 59, 999999)


def test_chaque_libelle_du_selecteur_donne_une_periode():
    """Le sélecteur de l'écran ne propose que ces quatre libellés"""
    for libelle in LIBELLES_PERIODES:
        periode = periode_depuis_libelle(libelle, UN_JOUR_DE_FEVRIER)

        assert periode.debut <= periode.fin


def test_libelle_inconnu_leve_une_erreur_plutot_que_de_choisir_une_periode():
    with pytest.raises(ValueError):
        periode_depuis_libelle("Depuis toujours", UN_JOUR_DE_FEVRIER)


def test_une_demande_du_mois_dernier_sort_du_mois_mais_reste_dans_lannee():
    """C'est le cas qui rend le sélecteur utile : le même jeu de données ne
    donne pas les mêmes chiffres selon la période choisie.
    """
    le_mois_dernier = datetime(2026, 1, 20)

    mois = periode_du_mois(UN_JOUR_DE_FEVRIER)
    annee = periode_de_lannee(UN_JOUR_DE_FEVRIER)

    assert not mois.debut <= le_mois_dernier <= mois.fin
    assert annee.debut <= le_mois_dernier <= annee.fin
