"""Pourquoi une prestation ne figure pas dans l'estimation

Le moteur signale qu'une catégorie n'a pas été chiffrée, sans dire pourquoi :
il ne connaît que l'absence de ressource retenue. Trois situations très
différentes se cachent derrière, et les confondre trompe le prospect —
l'écran annonçait « aucune salle ne peut accueillir 300 invités » alors que
des salles convenaient parfaitement mais qu'il n'en avait choisi aucune.
"""
from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue

# Le prospect en veut, mais rien au catalogue ne convient : l'entreprise chiffrera.
MOTIF_SUR_MESURE = "sur_mesure"
# Le catalogue ne propose rien du tout dans cette catégorie.
MOTIF_HORS_CATALOGUE = "hors_catalogue"
# Des options existaient, le prospect n'en a simplement retenu aucune.
MOTIF_NON_RETENUE = "non_retenue"


def qualifier_manque(
    besoin: Besoin, categorie: str, candidats: list[RessourceCatalogue]
) -> str:
    """Dit laquelle des trois situations explique l'absence de cette catégorie"""
    if categorie in besoin.categories_sur_mesure:
        return MOTIF_SUR_MESURE
    if not candidats:
        return MOTIF_HORS_CATALOGUE
    return MOTIF_NON_RETENUE


def regrouper_manques_par_motif(
    besoin: Besoin,
    categories_non_satisfaites: list[str],
    candidats_par_categorie: dict[str, list[RessourceCatalogue]],
) -> dict[str, list[str]]:
    """Range les catégories non chiffrées sous le motif qui les explique.

    Renvoyer un regroupement plutôt qu'une phrase laisse le canal écrire ce
    que le prospect lit, sans avoir à redécider quoi que ce soit.
    """
    regroupement: dict[str, list[str]] = {}
    for categorie in categories_non_satisfaites:
        motif = qualifier_manque(besoin, categorie, candidats_par_categorie.get(categorie, []))
        regroupement.setdefault(motif, []).append(categorie)
    return regroupement
