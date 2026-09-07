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


# Tranches fixes du mariage v1 (voir DONNEES.md : « trois ou quatre tranches »),
# calées sur le marché du mariage à Yaoundé, où 300 invités sont courants.
# Le triplet (nom, minimum, maximum) borne chaque tranche ; maximum=None pour la
# dernière, ouverte vers le haut. Une borne haute appartient à sa propre tranche
# et à elle seule : 250 invités tombent dans « 100-250 », 500 dans « 251-500 ».
TRANCHES_INVITES: tuple[tuple[str, int, int | None], ...] = (
    ("< 100", 1, 99),
    ("100-250", 100, 250),
    ("251-500", 251, 500),
    ("500+", 501, None),
)
