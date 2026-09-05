"""Calcul de la quantité d'une catégorie selon la règle du modèle d'événement"""
from src.moteur.types import BesoinChiffrage, RegleQuantite


def calculer_quantite(regle: RegleQuantite, besoin: BesoinChiffrage) -> int:
    """Calcule la quantité selon la base de la règle : par invité, par jour ou en forfait"""
    if regle.base == "invite":
        return besoin.nombre_invites * regle.multiplicateur
    if regle.base == "jour":
        return besoin.duree_jours * regle.multiplicateur
    if regle.base == "forfait":
        return regle.multiplicateur
    raise ValueError(f"base de règle de quantité inconnue : {regle.base}")
