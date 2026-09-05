"""Sélection des ressources candidates pour une catégorie du devis"""
from src.moteur.types import BesoinChiffrage, RessourceCatalogue

NOMBRE_MAX_OPTIONS_PAR_CATEGORIE = 3


def filtrer_salles_par_capacite(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Ne garde que les salles dont la capacité couvre le nombre d'invités"""
    return [salle for salle in salles if salle.attributs.get("capacite", 0) >= nombre_invites]


def trier_salles_par_quartier(
    salles: list[RessourceCatalogue], quartier_souhaite: str
) -> list[RessourceCatalogue]:
    """Remonte en tête les salles du quartier souhaité, sans en écarter aucune"""
    return sorted(salles, key=lambda salle: salle.attributs.get("quartier") != quartier_souhaite)


def rechercher_candidats_salle(
    salles: list[RessourceCatalogue], besoin: BesoinChiffrage
) -> list[RessourceCatalogue]:
    """Filtre les salles par capacité puis les trie par quartier souhaité (D17)"""
    salles_avec_capacite_suffisante = filtrer_salles_par_capacite(salles, besoin.nombre_invites)
    return trier_salles_par_quartier(salles_avec_capacite_suffisante, besoin.quartier_souhaite)


def trier_par_prix_croissant(ressources: list[RessourceCatalogue]) -> list[RessourceCatalogue]:
    """Trie les ressources du moins cher au plus cher"""
    return sorted(ressources, key=lambda ressource: ressource.prix_unitaire)


def limiter_nombre_options(
    ressources: list[RessourceCatalogue], nombre_max: int
) -> list[RessourceCatalogue]:
    """Ne garde que les nombre_max premières options"""
    return ressources[:nombre_max]


def rechercher_candidats_categorie(
    ressources_categorie: list[RessourceCatalogue],
    categorie: str,
    besoin: BesoinChiffrage,
) -> list[RessourceCatalogue]:
    """Applique la règle de sélection propre à la catégorie.

    La salle suit D17 (capacité puis quartier), sans limite de nombre. Les
    autres catégories sont triées par prix croissant et plafonnées à
    NOMBRE_MAX_OPTIONS_PAR_CATEGORIE pour ne pas noyer le prospect (D20).
    """
    if categorie == "salle":
        return rechercher_candidats_salle(ressources_categorie, besoin)
    ressources_triees = trier_par_prix_croissant(ressources_categorie)
    return limiter_nombre_options(ressources_triees, NOMBRE_MAX_OPTIONS_PAR_CATEGORIE)
