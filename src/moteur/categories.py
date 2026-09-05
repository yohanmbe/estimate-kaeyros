"""Résolution des catégories effectivement attendues pour une demande"""
from src.moteur.types import RegleQuantite


def resoudre_categories_attendues(
    modele: list[RegleQuantite],
    prestations_souhaitees: list[str],
    prestations_exclues: list[str],
) -> list[RegleQuantite]:
    """Ne garde du modèle que les catégories voulues par le prospect, retire celles exclues.

    Une liste de prestations souhaitées vide signifie que le prospect n'a
    restreint aucune catégorie : toutes celles du modèle s'appliquent, sauf
    celles explicitement exclues.
    """
    return [
        regle
        for regle in modele
        if regle.categorie not in prestations_exclues
        and (not prestations_souhaitees or regle.categorie in prestations_souhaitees)
    ]
