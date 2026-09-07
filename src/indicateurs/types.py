"""Structures de données des indicateurs du tableau de bord, voir DONNEES.md et D19"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Periode:
    """Bornes d'une période d'analyse choisie par le gestionnaire, toutes deux incluses"""

    debut: datetime
    fin: datetime


@dataclass(frozen=True)
class EffectifTranche:
    """Nombre de demandes dont le nombre d'invités tombe dans une tranche donnée"""

    tranche: str
    nombre_demandes: int


# Tranches fixes du mariage v1 (voir DONNEES.md : « trois ou quatre tranches »).
# Le triplet (nom, minimum, maximum) borne chaque tranche ; maximum=None pour la
# dernière, ouverte vers le haut.
TRANCHES_INVITES: tuple[tuple[str, int, int | None], ...] = (
    ("1-50", 1, 50),
    ("51-150", 51, 150),
    ("151-300", 151, 300),
    ("301+", 301, None),
)
