"""Enchaînement d'un tour de conversation : besoin, catalogue, décision, chiffrage

Seul endroit où le besoin extrait rencontre le catalogue du tenant. Il est
volontairement hors du canal : Streamlit aujourd'hui et WhatsApp demain
suivent le même parcours, seul l'affichage change (voir ARCHITECTURE.md,
« Le CANAL ne sait rien du métier »).
"""
from src.extraction.types import Besoin
from src.moteur.categories import resoudre_categories_attendues
from src.moteur.devis import chiffrer_devis
from src.moteur.selection import (
    rechercher_candidats_par_categorie,
    resoudre_ressources_choisies,
)
from src.moteur.types import (
    BesoinChiffrage,
    RegleQuantite,
    ResultatChiffrage,
    RessourceCatalogue,
)


def construire_besoin_chiffrage(besoin: Besoin) -> BesoinChiffrage | None:
    """Réduit le besoin aux champs du calcul, None tant qu'il en manque un.

    Le quartier et le budget peuvent rester absents : le premier ne fait que
    trier les salles (D17), le second ne fait que déclencher une alerte.
    """
    if besoin.nombre_invites is None or besoin.duree_jours is None:
        return None
    return BesoinChiffrage(
        nombre_invites=besoin.nombre_invites,
        duree_jours=besoin.duree_jours,
        quartier_souhaite=besoin.quartier_souhaite,
        budget_declare=besoin.budget_declare,
    )


def resoudre_modele_attendu(
    modele: list[RegleQuantite], besoin: Besoin
) -> list[RegleQuantite]:
    """Ne garde du modèle que les catégories que le prospect veut chiffrer"""
    return resoudre_categories_attendues(
        modele,
        list(besoin.prestations_souhaitees),
        list(besoin.prestations_exclues),
    )


def resoudre_candidats(
    besoin: Besoin,
    ressources: list[RessourceCatalogue],
    modele: list[RegleQuantite],
) -> dict[str, list[RessourceCatalogue]]:
    """Candidats par catégorie, vides tant que le besoin ne permet pas de sélectionner"""
    besoin_chiffrage = construire_besoin_chiffrage(besoin)
    if besoin_chiffrage is None:
        return {}
    return rechercher_candidats_par_categorie(
        ressources, resoudre_modele_attendu(modele, besoin), besoin_chiffrage
    )


def chiffrer_pour_besoin(
    besoin: Besoin,
    ressources: list[RessourceCatalogue],
    modele: list[RegleQuantite],
) -> ResultatChiffrage:
    """Chiffre le devis à partir du besoin complet et du catalogue du tenant"""
    besoin_chiffrage = construire_besoin_chiffrage(besoin)
    if besoin_chiffrage is None:
        raise ValueError("chiffrage demandé sur un besoin incomplet")
    candidats = resoudre_candidats(besoin, ressources, modele)
    return chiffrer_devis(
        resoudre_modele_attendu(modele, besoin),
        resoudre_ressources_choisies(candidats, besoin.ressources_choisies),
        besoin_chiffrage,
    )
