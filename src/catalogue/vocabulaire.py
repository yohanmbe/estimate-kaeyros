"""Vocabulaire du catalogue : catégories, unités de facturation et attributs.

Ressource.categorie et Ressource.unite_facturation sont des colonnes texte
libres en base (voir DONNEES.md) : rien au niveau du schéma n'empêche d'y
écrire n'importe quoi. Ce module est la seule source de vérité de ce qui est
accepté, et c'est à la frontière d'écriture que le contrôle se fait
(src/catalogue/edition.py), jamais par une contrainte de base.

SCHEMA_ATTRIBUTS décrit en plus ce que le dictionnaire attributs contient
selon la catégorie. C'est ce qui permet au formulaire du tableau de bord de
se construire en boucle sur la catégorie choisie, plutôt qu'avec une suite de
« si c'est une salle alors ». Et ça documente au même endroit les deux seuls
attributs que du code lit vraiment : capacite filtre les salles et quartier
les trie (voir src/moteur/selection.py et D17).
"""
from dataclasses import dataclass
from typing import Literal

CATEGORIES: tuple[str, ...] = (
    "salle",
    "mobilier",
    "restauration",
    "decoration",
    "sonorisation",
    "personnel",
    "logistique",
)

LIBELLES_CATEGORIES: dict[str, str] = {
    "salle": "salle",
    "mobilier": "mobilier",
    "restauration": "restauration",
    "decoration": "décoration",
    "sonorisation": "sonorisation",
    "personnel": "personnel",
    "logistique": "logistique",
}

UNITES_FACTURATION: tuple[str, ...] = ("jour", "unite", "personne", "forfait", "heure")

LIBELLES_UNITES: dict[str, str] = {
    "jour": "par jour",
    "unite": "l'unité",
    "personne": "par personne",
    "forfait": "au forfait",
    "heure": "par heure",
}

# Unité la plus courante pour chaque catégorie, telle que le catalogue de
# démonstration la facture. Sert uniquement à présélectionner le bon choix
# dans le formulaire : le gestionnaire reste libre d'en changer.
UNITE_HABITUELLE: dict[str, str] = {
    "salle": "jour",
    "mobilier": "unite",
    "restauration": "personne",
    "decoration": "forfait",
    "sonorisation": "forfait",
    "personnel": "forfait",
    "logistique": "forfait",
}


@dataclass(frozen=True)
class ChampAttribut:
    """Un champ du dictionnaire attributs, tel que le formulaire doit le demander"""

    cle: str
    libelle: str
    nature: Literal["texte", "entier"]
    obligatoire: bool
    aide: str | None = None


# Seules les catégories qui portent des attributs figurent ici ; les autres
# n'en ont aucun et passent par champs_attributs, qui renvoie un tuple vide.
SCHEMA_ATTRIBUTS: dict[str, tuple[ChampAttribut, ...]] = {
    "salle": (
        ChampAttribut(
            cle="capacite",
            libelle="Capacité",
            nature="entier",
            obligatoire=True,
            aide="Nombre maximum d'invités que cette salle peut accueillir.",
        ),
        ChampAttribut(
            cle="quartier",
            libelle="Quartier",
            nature="texte",
            obligatoire=True,
            aide="Quartier où se trouve la salle. Elle sera mise en avant "
            "quand un prospect demande ce quartier.",
        ),
    ),
    "mobilier": (
        ChampAttribut(
            cle="style",
            libelle="Style",
            nature="texte",
            obligatoire=False,
            aide="Détail visible par le prospect, par exemple « Napoléon doré ».",
        ),
    ),
}


def libelle_categorie(categorie: str) -> str:
    """Nom affichable d'une catégorie de ressource"""
    return LIBELLES_CATEGORIES.get(categorie, categorie)


def libelle_unite(unite: str) -> str:
    """Nom affichable d'une unité de facturation"""
    return LIBELLES_UNITES.get(unite, unite)


def champs_attributs(categorie: str) -> tuple[ChampAttribut, ...]:
    """Champs d'attributs attendus pour cette catégorie, vide si elle n'en a aucun"""
    return SCHEMA_ATTRIBUTS.get(categorie, ())
