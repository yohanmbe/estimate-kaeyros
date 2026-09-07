"""Contenu des questions posées au prospect

Le contenu est décidé ici, en Python, à partir de ce qui manque au besoin.
Le LLM ne fait que le reformuler en français naturel (voir D01) : il ne
choisit ni la question, ni le moment où elle est posée.
"""

LIBELLES_CHAMPS: dict[str, str] = {
    "type_evenement": "le type d'événement",
    "nombre_invites": "le nombre d'invités",
    "duree_jours": "la durée en jours",
    "ville": "la ville",
    "date_evenement": "la date",
}


def formuler_question_besoin(champs_manquants: tuple[str, ...]) -> str:
    """Compose une seule question couvrant tous les champs manquants.

    Pas de préambule fixe (« pour préparer votre estimation... ») : répété à
    chaque tour, il finit par lasser. Le contenu va droit au but, la
    reformulation se charge de le rendre naturel.
    """
    libelles = [LIBELLES_CHAMPS.get(champ, champ) for champ in champs_manquants]
    return f"Il me manque {enumerer(libelles)}."


def enumerer(elements: list[str]) -> str:
    """Assemble une énumération française : a, b et c"""
    if len(elements) == 1:
        return elements[0]
    return f"{', '.join(elements[:-1])} et {elements[-1]}"
