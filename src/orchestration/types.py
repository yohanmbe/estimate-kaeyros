"""Décisions que peut renvoyer la machine à états (voir machine.py)"""
from dataclasses import dataclass

from src.moteur.types import RessourceCatalogue


@dataclass(frozen=True)
class QuestionBesoin:
    """Il manque des champs obligatoires : une question groupée les couvre tous"""

    champs_manquants: tuple[str, ...]


@dataclass(frozen=True)
class QuestionConfirmation:
    """L'extracteur a déduit une valeur au lieu de la lire : le prospect tranche.

    Une seule valeur proposée = « c'est bien ça ? ». Plusieurs = « laquelle ? »,
    le cas de « ce weekend » qui désigne un samedi et un dimanche.
    """

    champ: str
    valeurs_proposees: tuple[str, ...]


@dataclass(frozen=True)
class QuestionChoixRessources:
    """Une catégorie a un ou plusieurs candidats que le prospect n'a pas encore tranchés.

    Même à candidat unique, rien n'entre au devis sans son accord explicite.
    Une seule catégorie à la fois, jamais groupées : ce choix se fait par
    sélection directe dans le canal (boutons, liste), sans passer par le
    LLM, donc rien à gagner à réduire le nombre de tours (voir D04).

    devis_sur_mesure_possible signale que le catalogue ne répond pas bien au
    besoin — rien à proposer, salle trop petite ou démesurée : le prospect
    peut alors demander une proposition à l'entreprise plutôt que de choisir
    dans une liste qui ne lui convient pas.
    """

    categorie: str
    candidats: list[RessourceCatalogue]
    devis_sur_mesure_possible: bool = False


@dataclass(frozen=True)
class QuestionComplements:
    """Dernière étape avant l'estimation : ce qui manque au catalogue, et un mot libre.

    Posée une seule fois, juste avant le chiffrage, quand tous les choix sont
    faits : c'est le moment où le prospect voit ce que l'estimation va
    contenir et peut dire ce qui lui manque encore.
    """


@dataclass(frozen=True)
class PassageChiffrage:
    """Le besoin est complet et tous les choix de ressources sont résolus"""


Decision = (
    QuestionBesoin
    | QuestionConfirmation
    | QuestionChoixRessources
    | QuestionComplements
    | PassageChiffrage
)
