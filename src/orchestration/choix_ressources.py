"""Identification de la prochaine catégorie dont le choix de ressource est en attente

Une catégorie avec un seul candidat est retenue automatiquement en amont
(il n'y a rien à décider) : elle n'est jamais renvoyée ici.

Une seule catégorie à la fois, jamais groupées : contrairement au besoin
(voir champs_obligatoires.py), ce choix se fait par sélection directe dans
le canal, sans appel au LLM. Regrouper ne ferait gagner aucun appel, donc
inutile de complexifier l'échange.
"""
from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue


def identifier_prochaine_categorie_a_choisir(
    besoin: Besoin,
    candidats_par_categorie: dict[str, list[RessourceCatalogue]],
) -> tuple[str, list[RessourceCatalogue]] | None:
    """Première catégorie à choix multiple que le prospect n'a pas encore tranchée"""
    for categorie, candidats in candidats_par_categorie.items():
        if len(candidats) >= 2 and not _un_candidat_deja_choisi(candidats, besoin):
            return categorie, candidats
    return None


def _un_candidat_deja_choisi(candidats: list[RessourceCatalogue], besoin: Besoin) -> bool:
    """Vrai si le prospect a déjà choisi une des ressources candidates de la catégorie"""
    return any(candidat.id in besoin.ressources_choisies for candidat in candidats)
