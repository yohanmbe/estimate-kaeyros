"""Sélection des ressources candidates pour une catégorie du devis"""
from src.moteur.types import BesoinChiffrage, RegleQuantite, RessourceCatalogue

NOMBRE_MAX_OPTIONS_PAR_CATEGORIE = 3


def filtrer_salles_par_capacite(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Ne garde que les salles dont la capacité couvre le nombre d'invités"""
    return [salle for salle in salles if salle.attributs.get("capacite", 0) >= nombre_invites]


def trier_salles_par_quartier(
    salles: list[RessourceCatalogue], quartier_souhaite: str | None
) -> list[RessourceCatalogue]:
    """Remonte en tête les salles du quartier souhaité, sans en écarter aucune.

    Sans quartier souhaité, aucune préférence à appliquer : l'ordre reçu
    (déjà filtré par capacité) est conservé tel quel.
    """
    if quartier_souhaite is None:
        return list(salles)
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


def rechercher_candidats_par_categorie(
    ressources: list[RessourceCatalogue],
    modele: list[RegleQuantite],
    besoin: BesoinChiffrage,
) -> dict[str, list[RessourceCatalogue]]:
    """Résout les candidats de chaque catégorie attendue, dans l'ordre du modèle.

    Une catégorie sans aucun candidat reste présente avec une liste vide :
    c'est ce qui permet de l'annoncer au prospect plutôt que de la passer
    sous silence (cas d'une salle trop petite pour le nombre d'invités).
    """
    return {
        regle.categorie: rechercher_candidats_categorie(
            [ressource for ressource in ressources if ressource.categorie == regle.categorie],
            regle.categorie,
            besoin,
        )
        for regle in modele
    }


def resoudre_ressources_choisies(
    candidats_par_categorie: dict[str, list[RessourceCatalogue]],
    ids_choisis: tuple[str, ...],
) -> dict[str, RessourceCatalogue]:
    """Associe à chaque catégorie la ressource retenue pour le chiffrage.

    Une catégorie à candidat unique est retenue d'office : il n'y a rien à
    décider. Une catégorie sans candidat reste absente du résultat, le moteur
    la signalera comme non satisfaite.
    """
    retenues: dict[str, RessourceCatalogue] = {}
    for categorie, candidats in candidats_par_categorie.items():
        choisie = _trouver_candidat_choisi(candidats, ids_choisis)
        if choisie is not None:
            retenues[categorie] = choisie
        elif len(candidats) == 1:
            retenues[categorie] = candidats[0]
    return retenues


def _trouver_candidat_choisi(
    candidats: list[RessourceCatalogue], ids_choisis: tuple[str, ...]
) -> RessourceCatalogue | None:
    """Candidat de la catégorie que le prospect a explicitement choisi"""
    return next((candidat for candidat in candidats if candidat.id in ids_choisis), None)
