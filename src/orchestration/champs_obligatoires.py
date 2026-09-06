"""Identification des champs obligatoires encore manquants dans le besoin

Le quartier n'en fait pas partie : il sert uniquement à trier les salles
(D17), jamais à filtrer ni à bloquer le chiffrage.
"""
from src.extraction.types import Besoin

CHAMPS_OBLIGATOIRES: tuple[str, ...] = (
    "type_evenement",
    "nombre_invites",
    "duree_jours",
    "ville",
    "date_evenement",
)


def identifier_champs_obligatoires_manquants(besoin: Besoin) -> tuple[str, ...]:
    """Renvoie les champs obligatoires absents du besoin, dans l'ordre de priorité"""
    return tuple(champ for champ in CHAMPS_OBLIGATOIRES if getattr(besoin, champ) is None)
