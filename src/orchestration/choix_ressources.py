"""Identification de la prochaine catégorie dont le choix de ressource est en attente

Toute catégorie avec au moins un candidat doit être tranchée par le
prospect, même à candidat unique : rien n'entre dans le devis sans son
accord explicite, y compris une catégorie où il n'y a qu'une option (il
peut encore la refuser). Seule une catégorie sans aucun candidat échappe à
ce choix, faute d'avoir quoi que ce soit à proposer.

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
    """Première catégorie ayant un candidat que le prospect n'a pas encore tranchée"""
    categories_en_attente = identifier_categories_restant_a_choisir(besoin, candidats_par_categorie)
    if not categories_en_attente:
        return None
    premiere = categories_en_attente[0]
    return premiere, candidats_par_categorie[premiere]


def identifier_categories_restant_a_choisir(
    besoin: Besoin,
    candidats_par_categorie: dict[str, list[RessourceCatalogue]],
) -> list[str]:
    """Toutes les catégories ayant un candidat encore en attente, pas seulement la première.

    Sert à l'arrêt anticipé du parcours (« j'ai tout ce qu'il me faut ») : le
    prospect peut arrêter de choisir avant d'avoir parcouru tout le catalogue,
    et ces catégories sont alors exclues d'un bloc plutôt qu'une par une —
    y compris celles à candidat unique, qui n'ont sinon jamais été tranchées.
    """
    return [
        categorie
        for categorie, candidats in candidats_par_categorie.items()
        if len(candidats) >= 1 and not _un_candidat_deja_choisi(candidats, besoin)
    ]


def _un_candidat_deja_choisi(candidats: list[RessourceCatalogue], besoin: Besoin) -> bool:
    """Vrai si le prospect a déjà choisi une des ressources candidates de la catégorie"""
    return any(candidat.id in besoin.ressources_choisies for candidat in candidats)
