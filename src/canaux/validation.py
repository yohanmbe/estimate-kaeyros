"""Validation légère des champs du formulaire prospect (voir streamlit_prospect.py)

Volontairement permissive : pas de validation par pays ni de vérification
d'existence, juste de quoi écarter une saisie manifestement fausse (lettres
dans un numéro, email sans arobase). C'est un formulaire, pas un service de
vérification d'identité.
"""
import re

MOTIF_TELEPHONE = re.compile(r"^\+?\d{8,15}$")
MOTIF_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def telephone_valide(telephone: str) -> bool:
    """Vrai si le numéro, une fois les séparateurs courants retirés, a 8 à 15 chiffres"""
    sans_separateurs = re.sub(r"[ .\-()]", "", telephone)
    return bool(MOTIF_TELEPHONE.match(sans_separateurs))


def email_valide(email: str) -> bool:
    """Vrai si l'email a la forme minimale texte@texte.texte"""
    return bool(MOTIF_EMAIL.match(email))
