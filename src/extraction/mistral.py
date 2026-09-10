"""Implémentation de InterfaceLLM qui appelle l'API Mistral AI (palier gratuit Experiment)

Ce module ne porte que le dialogue avec l'API : les consignes envoyées au
modèle vivent dans instructions.py, la validation de sa réponse dans
reponse.py, tous deux partagés avec les autres fournisseurs.

Aucune erreur de ce module ne doit interrompre la conversation : un appel
raté ou une réponse mal formée renvoie simplement le besoin ou le texte
d'entrée inchangé, après avoir loggé le détail pour le débogage.
"""
import logging
import os

import httpx
from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.errors import MistralError, NoResponseError

from src.extraction.instructions import (
    INSTRUCTIONS_EXTRACTION,
    INSTRUCTIONS_REFORMULATION,
    construire_contenu_utilisateur,
)
from src.extraction.interface import InterfaceLLM
from src.extraction.reponse import contient_un_nombre_invente, parser_besoin
from src.extraction.types import Besoin

load_dotenv()
logger = logging.getLogger(__name__)

MODELE = "mistral-small-latest"

ERREURS_APPEL_MISTRAL = (MistralError, NoResponseError, httpx.HTTPError)

# Voir groq.py : un réessai suffit presque toujours face à un JSON tronqué,
# et évite de perdre en silence ce que le prospect vient de dire.
NOMBRE_TENTATIVES_EXTRACTION = 2


class ExtracteurMistral(InterfaceLLM):
    """Implémentation réelle de InterfaceLLM, via l'API Mistral AI"""

    def __init__(self) -> None:
        cle_api = os.getenv("MISTRAL_API_KEY")
        if not cle_api or not cle_api.strip():
            raise RuntimeError("MISTRAL_API_KEY manquante ou vide : vérifie le fichier .env")
        self._client = Mistral(api_key=cle_api)

    def extraire_besoin(self, message: str, besoin_actuel: Besoin) -> Besoin:
        """Demande au modèle le besoin mis à jour ; renvoie le besoin actuel si toutes les tentatives échouent"""
        contenu_utilisateur = construire_contenu_utilisateur(message, besoin_actuel)
        for tentative in range(1, NOMBRE_TENTATIVES_EXTRACTION + 1):
            try:
                reponse = self._client.chat.complete(
                    model=MODELE,
                    messages=[
                        {"role": "system", "content": INSTRUCTIONS_EXTRACTION},
                        {"role": "user", "content": contenu_utilisateur},
                    ],
                    response_format={"type": "json_object"},
                )
            except ERREURS_APPEL_MISTRAL as erreur:
                logger.error(
                    "Appel Mistral échoué lors de l'extraction du besoin (tentative %d/%d) : %s",
                    tentative, NOMBRE_TENTATIVES_EXTRACTION, erreur,
                )
                continue

            contenu_brut = reponse.choices[0].message.content
            besoin_extrait = parser_besoin(contenu_brut, message)
            if besoin_extrait is not None:
                return besoin_extrait
            logger.error(
                "Réponse Mistral invalide lors de l'extraction du besoin (tentative %d/%d), contenu reçu : %r",
                tentative, NOMBRE_TENTATIVES_EXTRACTION, contenu_brut,
            )

        return besoin_actuel

    def reformuler(self, contenu: str) -> str:
        """Demande au modèle de reformuler ; renvoie le contenu d'entrée si l'appel échoue"""
        try:
            reponse = self._client.chat.complete(
                model=MODELE,
                messages=[
                    {"role": "system", "content": INSTRUCTIONS_REFORMULATION},
                    {"role": "user", "content": contenu},
                ],
            )
        except ERREURS_APPEL_MISTRAL as erreur:
            logger.error("Appel Mistral échoué lors de la reformulation : %s", erreur)
            return contenu

        contenu_reformule = reponse.choices[0].message.content
        if not isinstance(contenu_reformule, str) or not contenu_reformule.strip():
            logger.error(
                "Réponse Mistral invalide lors de la reformulation, contenu reçu : %r", contenu_reformule
            )
            return contenu
        if contient_un_nombre_invente(contenu, contenu_reformule):
            logger.error(
                "Reformulation Mistral rejetée, nombre inventé absent de la source : %r -> %r",
                contenu, contenu_reformule,
            )
            return contenu
        return contenu_reformule
