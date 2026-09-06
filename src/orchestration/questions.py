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

LIBELLES_CATEGORIES: dict[str, str] = {
    "salle": "salle",
    "mobilier": "mobilier",
    "restauration": "restauration",
    "decoration": "décoration",
    "sonorisation": "sonorisation",
    "personnel": "personnel",
    "logistique": "logistique",
}


def formuler_question_besoin(champs_manquants: tuple[str, ...]) -> str:
    """Compose une seule question couvrant tous les champs manquants"""
    libelles = [LIBELLES_CHAMPS.get(champ, champ) for champ in champs_manquants]
    return f"Pour préparer votre estimation, il me manque {enumerer(libelles)}."


def libelle_categorie(categorie: str) -> str:
    """Nom affichable d'une catégorie de ressource"""
    return LIBELLES_CATEGORIES.get(categorie, categorie)


def enumerer(elements: list[str]) -> str:
    """Assemble une énumération française : a, b et c"""
    if len(elements) == 1:
        return elements[0]
    return f"{', '.join(elements[:-1])} et {elements[-1]}"
