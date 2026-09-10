"""Mise en forme d'une date pour l'affichage, partagée par tous les canaux.

Les noms de jours et de mois sont écrits ici plutôt que tirés de la locale du
système : la locale dépend de la machine qui exécute le programme, et un
serveur configuré en anglais afficherait « saturday » au prospect.
"""
from datetime import date

JOURS_SEMAINE = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")

MOIS = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)


def formater_date_lisible(valeur: str | None) -> str:
    """Transforme une date canonique en français lisible : « samedi 12 septembre 2026 ».

    Une valeur qui n'est pas au format canonique est renvoyée telle quelle :
    c'est le cas d'une date que le modèle n'a pas su interpréter, qu'on
    préfère montrer au prospect dans ses propres mots plutôt que d'effacer.
    """
    if valeur is None:
        return ""
    try:
        jour = date.fromisoformat(valeur)
    except ValueError:
        return valeur
    return f"{JOURS_SEMAINE[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]} {jour.year}"
