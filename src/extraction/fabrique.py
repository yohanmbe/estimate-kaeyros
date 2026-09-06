"""Choix de l'implémentation de InterfaceLLM d'après la variable LLM_PROVIDER

Le canal ne nomme aucun fournisseur : il demande un extracteur, cette fabrique
décide lequel construire. Revenir au mock ou basculer vers un autre fournisseur
se fait dans .env, sans toucher au code des autres couches. C'est ce que le
passage de Mistral à Groq avait déjà validé en pratique (voir D20).

Chaque fournisseur est importé à l'intérieur de sa fonction : charger le module
d'un fournisseur inutilisé imposerait son paquet et sa clé d'API à tout le
monde, alors qu'un seul sert à la fois.
"""
import os

from dotenv import load_dotenv

from src.extraction.interface import InterfaceLLM

FOURNISSEUR_MOCK = "mock"
FOURNISSEUR_PAR_DEFAUT = "groq"


def _construire_groq() -> InterfaceLLM:
    """Fournisseur réel retenu en v1 (voir D20)"""
    from src.extraction.groq import ExtracteurGroq

    return ExtracteurGroq()


def _construire_mistral() -> InterfaceLLM:
    """Fournisseur conservé : son palier gratuit s'est révélé inutilisable (voir D20)"""
    from src.extraction.mistral import ExtracteurMistral

    return ExtracteurMistral()


def _construire_mock() -> InterfaceLLM:
    """Aucun appel réseau : sert à la démonstration et aux tests"""
    from src.extraction.mock import ExtracteurMock

    return ExtracteurMock()


# Ajouter un fournisseur revient à écrire sa fonction et à l'inscrire ici.
FABRIQUES = {
    FOURNISSEUR_PAR_DEFAUT: _construire_groq,
    "mistral": _construire_mistral,
    FOURNISSEUR_MOCK: _construire_mock,
}


def fournisseur_actif() -> str:
    """Nom du fournisseur configuré dans LLM_PROVIDER, groq à défaut.

    Un nom inconnu est refusé plutôt que remplacé silencieusement : une faute
    de frappe ferait autrement basculer la conversation sur un autre
    fournisseur sans que personne ne s'en aperçoive.
    """
    load_dotenv()
    fournisseur = (os.getenv("LLM_PROVIDER") or FOURNISSEUR_PAR_DEFAUT).strip().lower()
    if fournisseur not in FABRIQUES:
        raise RuntimeError(
            f"LLM_PROVIDER inconnu : {fournisseur!r}. "
            f"Valeurs acceptées : {', '.join(FABRIQUES)}."
        )
    return fournisseur


def construire_extracteur() -> InterfaceLLM:
    """Construit l'extracteur du fournisseur configuré"""
    return FABRIQUES[fournisseur_actif()]()
