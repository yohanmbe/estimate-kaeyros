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

    # Catégories pour lesquelles le prospect demande une proposition de
    # l'entreprise : il en veut, mais rien au catalogue ne lui convient.
    # À distinguer de prestations_exclues, où il n'en veut simplement pas.
    categories_sur_mesure: tuple[str, ...] = field(default_factory=tuple)

    # Ce que l'extracteur a déduit plutôt que lu, et ce que le prospect a
    # tranché. L'extracteur signale, il ne demande rien : c'est
    # l'orchestrateur qui décide de poser la question (voir D01, D04).
    dates_possibles: tuple[str, ...] = field(default_factory=tuple)
    champs_a_confirmer: tuple[str, ...] = field(default_factory=tuple)
    champs_confirmes: tuple[str, ...] = field(default_factory=tuple)

    # Le champ que le prospect vient de démentir : tant qu'il est vide, c'est
    # la seule chose qu'on lui redemande. Sans ça, dire « ce n'est pas la
    # date » déclenchait la liste de tout ce qui manque, ou pire une question
    # sur autre chose.
    champ_en_correction: str | None = None
