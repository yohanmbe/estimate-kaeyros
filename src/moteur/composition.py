"""Composition des lignes du devis à partir des ressources choisies"""
from src.moteur.quantites import calculer_quantite
from src.moteur.types import (
    BesoinChiffrage,
    CategorieNonSatisfaite,
    LigneDevis,
    RegleQuantite,
    RessourceCatalogue,
)


def composer_ligne(ressource: RessourceCatalogue, quantite: int) -> LigneDevis:
    """Construit une ligne de devis à partir d'une ressource choisie et d'une quantité"""
    return LigneDevis(
        designation=ressource.nom,
        quantite=quantite,
        prix_unitaire=ressource.prix_unitaire,
        montant=ressource.prix_unitaire * quantite,
        ressource_id=ressource.id,
    )


def composer_devis(
    modele: list[RegleQuantite],
    ressources_choisies: dict[str, RessourceCatalogue],
    besoin: BesoinChiffrage,
) -> tuple[list[LigneDevis], list[CategorieNonSatisfaite]]:
    """Parcourt les catégories attendues, compose une ligne si une ressource est choisie, sinon la signale"""
    lignes: list[LigneDevis] = []
    categories_non_satisfaites: list[CategorieNonSatisfaite] = []
    for regle in modele:
        ressource = ressources_choisies.get(regle.categorie)
        if ressource is None:
            categories_non_satisfaites.append(CategorieNonSatisfaite(categorie=regle.categorie))
            continue
        quantite = calculer_quantite(regle, besoin)
        lignes.append(composer_ligne(ressource, quantite))
    return lignes, categories_non_satisfaites
