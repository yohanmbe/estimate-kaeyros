"""Décisions que peut renvoyer la machine à états (voir machine.py)"""
from dataclasses import dataclass

from src.moteur.types import RessourceCatalogue


@dataclass(frozen=True)
class QuestionBesoin:
    """Il manque des champs obligatoires : une question groupée les couvre tous"""

    champs_manquants: tuple[str, ...]


@dataclass(frozen=True)
class QuestionChoixRessources:
    """Une catégorie a plusieurs ressources candidates non encore choisies.

    Une seule catégorie à la fois, jamais groupées : ce choix se fait par
    sélection directe dans le canal (boutons, liste), sans passer par le
    LLM, donc rien à gagner à réduire le nombre de tours (voir D04).
    """

    categorie: str
    candidats: list[RessourceCatalogue]


@dataclass(frozen=True)
class PassageChiffrage:
    """Le besoin est complet et tous les choix de ressources sont résolus"""


Decision = QuestionBesoin | QuestionChoixRessources | PassageChiffrage
