"""Contenu des questions posées au prospect

Le contenu est décidé ici, en Python, à partir de ce qui manque au besoin.
Le LLM ne fait que le reformuler en français naturel (voir D01) : il ne
choisit ni la question, ni le moment où elle est posée.
"""

from src.catalogue.vocabulaire import libelle_categorie
from src.extraction.types import Besoin
from src.presentation.dates import formater_date_lisible

LIBELLES_CHAMPS: dict[str, str] = {
    "type_evenement": "le type d'événement",
    "nombre_invites": "le nombre d'invités",
    "duree_jours": "la durée en jours",
    "ville": "la ville",
    "date_evenement": "la date",
}

# Les champs dont la valeur est une date sont réécrits en français lisible
# avant d'être montrés : « 2026-09-12 » ne se relit pas à voix haute.
CHAMPS_DATE = ("date_evenement",)

QUESTIONS_CONFIRMATION: dict[str, str] = {
    "type_evenement": "Votre événement est bien un {valeur} ?",
    "date_evenement": "Votre événement a bien lieu le {valeur} ?",
    "ville": "Votre événement a bien lieu à {valeur} ?",
    "quartier_souhaite": "Vous cherchez bien un lieu du côté de {valeur} ?",
    "nombre_invites": "Vous attendez bien {valeur} invités ?",
    "duree_jours": "Votre événement dure bien {valeur} jour(s) ?",
    "budget_declare": "Votre budget est bien de {valeur} ?",
}

QUESTIONS_CHOIX_ENTRE_VALEURS: dict[str, str] = {
    "date_evenement": "Quelle date retenez-vous : {valeurs} ?",
}


def formuler_question_besoin(champs_manquants: tuple[str, ...]) -> str:
    """Compose une seule question couvrant tous les champs manquants.

    Pas de préambule fixe (« pour préparer votre estimation... ») : répété à
    chaque tour, il finit par lasser. Le contenu va droit au but, la
    reformulation se charge de le rendre naturel.
    """
    libelles = [LIBELLES_CHAMPS.get(champ, champ) for champ in champs_manquants]
    return f"Il me manque {enumerer(libelles)}."


def formuler_question_choix(
    categorie: str,
    nombre_candidats: int,
    besoin: Besoin,
    devis_sur_mesure_possible: bool = False,
) -> str:
    """Compose un bloc qui rappelle l'événement, dit ce qui est proposé, et ce qu'on attend.

    Le prospect a décrit son événement plusieurs messages plus haut : sans ce
    rappel, il voit surgir une liste de salles sans savoir sur quelle base
    elle a été établie, ni pourquoi celle-ci et pas une autre.
    """
    debut = f"Pour {_resume_evenement(besoin)}"
    if nombre_candidats == 0:
        return (
            f"{debut}, aucune option de {libelle_categorie(categorie)} du catalogue "
            "ne convient. Vous pouvez demander une proposition sur mesure, "
            "ou passer cette prestation."
        )

    options = (
        f"voici {nombre_candidats} option{'s' if nombre_candidats > 1 else ''} "
        f"de {libelle_categorie(categorie)}"
    )
    fin = (
        "Choisissez celle qui vous convient, demandez une proposition sur mesure, "
        "ou passez cette prestation."
        if devis_sur_mesure_possible
        else "Choisissez celle qui vous convient, ou passez cette prestation."
    )
    return f"{debut}, {options}. {fin}"


def _resume_evenement(besoin: Besoin) -> str:
    """Rappelle en une phrase ce sur quoi porte l'estimation"""
    morceaux = []
    if besoin.nombre_invites is not None:
        morceaux.append(f"{besoin.nombre_invites} invités")
    if besoin.ville:
        morceaux.append(f"à {besoin.ville}")
    if besoin.duree_jours is not None:
        morceaux.append(f"sur {besoin.duree_jours} jour(s)")
    return " ".join(morceaux) if morceaux else "votre événement"


def formuler_question_confirmation(champ: str, valeurs_proposees: tuple[str, ...]) -> str:
    """Compose la question qui fait trancher une hypothèse de l'extracteur.

    Une seule valeur se confirme (« c'est bien ça ? »), plusieurs se
    choisissent (« laquelle ? »). Dans les deux cas la valeur est affichée
    telle que le prospect la lira, jamais sous sa forme technique.
    """
    valeurs_lisibles = [_valeur_lisible(champ, valeur) for valeur in valeurs_proposees]

    if len(valeurs_lisibles) == 1:
        modele = QUESTIONS_CONFIRMATION.get(champ, "Vous confirmez : {valeur} ?")
        return modele.format(valeur=valeurs_lisibles[0])

    modele = QUESTIONS_CHOIX_ENTRE_VALEURS.get(champ, "Laquelle retenez-vous : {valeurs} ?")
    return modele.format(valeurs=enumerer_alternatives(valeurs_lisibles))


def _valeur_lisible(champ: str, valeur: str) -> str:
    """Réécrit une valeur pour le prospect : une date en toutes lettres, le reste tel quel"""
    if champ in CHAMPS_DATE:
        return formater_date_lisible(valeur)
    return valeur


def enumerer(elements: list[str]) -> str:
    """Assemble une énumération française : a, b et c"""
    if len(elements) == 1:
        return elements[0]
    return f"{', '.join(elements[:-1])} et {elements[-1]}"


def enumerer_alternatives(elements: list[str]) -> str:
    """Assemble une énumération de choix exclusifs : a, b ou c"""
    if len(elements) == 1:
        return elements[0]
    return f"{', '.join(elements[:-1])} ou {elements[-1]}"
