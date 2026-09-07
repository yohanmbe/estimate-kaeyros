"""Mise en forme d'un montant pour l'affichage, partagée par tous les canaux.

Un seul endroit décide à quoi ressemble un montant : le chat du prospect, le PDF
du devis et le tableau de bord du gestionnaire l'écrivent tous pareil. Ce module
ne calcule rien, il met en forme un entier déjà produit par le moteur (voir D01).
"""

# Espace insécable, écrit en échappement plutôt qu'en caractère littéral qui
# serait invisible à la relecture. Un montant ne doit se couper en fin de ligne
# ni entre ses milliers, ni avant sa devise.
ESPACE_INSECABLE = "\u00a0"

DEVISE = "FCFA"


def formater_montant(montant: int) -> str:
    """Montant entier suivi de sa devise, toujours explicite (voir CLAUDE.md)"""
    return f"{formater_nombre(montant)}{ESPACE_INSECABLE}{DEVISE}"


def formater_nombre(valeur: int) -> str:
    """Entier avec ses milliers séparés, sans devise : un nombre d'invités par exemple"""
    return f"{valeur:,}".replace(",", ESPACE_INSECABLE)
