"""Périodes d'analyse proposées au gestionnaire.

Le tableau de bord n'offre pas un calendrier libre mais trois périodes usuelles.
Elles sont calculées ici, à partir d'une date passée en paramètre plutôt que
lue de l'horloge à l'intérieur : c'est ce qui rend le calcul testable sans
dépendre du jour où les tests tournent.

Les bornes couvrent la période entière, du premier jour à minuit au dernier
jour à la dernière microseconde, et non « jusqu'à maintenant » : deux
consultations le même jour donnent ainsi le même chiffre.
"""
from calendar import monthrange
from datetime import date, datetime

from src.indicateurs.types import Periode

LIBELLE_MOIS = "Ce mois"
LIBELLE_TRIMESTRE = "Ce trimestre"
LIBELLE_ANNEE = "Cette année"

LIBELLES_PERIODES: tuple[str, ...] = (LIBELLE_MOIS, LIBELLE_TRIMESTRE, LIBELLE_ANNEE)

MOIS_PAR_TRIMESTRE = 3


def periode_du_mois(aujourdhui: date) -> Periode:
    """Du premier au dernier jour du mois courant"""
    return _bornes(aujourdhui.year, aujourdhui.month, aujourdhui.month)


def periode_du_trimestre(aujourdhui: date) -> Periode:
    """Des trois mois du trimestre courant, janvier-mars pour un jour de février"""
    premier_mois = MOIS_PAR_TRIMESTRE * ((aujourdhui.month - 1) // MOIS_PAR_TRIMESTRE) + 1
    return _bornes(aujourdhui.year, premier_mois, premier_mois + MOIS_PAR_TRIMESTRE - 1)


def periode_de_lannee(aujourdhui: date) -> Periode:
    """Du 1er janvier au 31 décembre de l'année courante"""
    return _bornes(aujourdhui.year, 1, 12)


def periode_depuis_libelle(libelle: str, aujourdhui: date) -> Periode:
    """Période correspondant au libellé choisi dans le sélecteur de l'écran"""
    calculs = {
        LIBELLE_MOIS: periode_du_mois,
        LIBELLE_TRIMESTRE: periode_du_trimestre,
        LIBELLE_ANNEE: periode_de_lannee,
    }
    if libelle not in calculs:
        raise ValueError(f"période inconnue : {libelle}")
    return calculs[libelle](aujourdhui)


def _bornes(annee: int, premier_mois: int, dernier_mois: int) -> Periode:
    """Période allant du premier jour du premier mois au dernier jour du dernier"""
    dernier_jour = monthrange(annee, dernier_mois)[1]
    return Periode(
        debut=datetime(annee, premier_mois, 1),
        fin=datetime(annee, dernier_mois, dernier_jour, 23, 59, 59, 999999),
    )
