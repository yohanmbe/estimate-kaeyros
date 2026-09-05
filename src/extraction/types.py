"""Structure du besoin extrait au fil de la conversation (voir DONNEES.md)"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Besoin:
    """Besoin structuré, tel que stocké dans Demande.besoin.

    Chaque champ est optionnel : le besoin se construit progressivement,
    message après message. L'orchestrateur, pas l'extracteur, décide quand
    il est suffisamment complet pour passer au chiffrage.
    """

    type_evenement: str | None = None
    date_evenement: str | None = None
    ville: str | None = None
    quartier_souhaite: str | None = None
    nombre_invites: int | None = None
    duree_jours: int | None = None
    budget_declare: int | None = None
    prestations_souhaitees: tuple[str, ...] = field(default_factory=tuple)
    prestations_exclues: tuple[str, ...] = field(default_factory=tuple)
    ressources_choisies: tuple[str, ...] = field(default_factory=tuple)
