"""Implémentation de InterfaceLLM qui appelle l'API Mistral AI (palier gratuit Experiment)

Aucune erreur de ce module ne doit interrompre la conversation : un appel
raté ou une réponse mal formée renvoie simplement le besoin ou le texte
d'entrée inchangé, après avoir loggé le détail pour le débogage.
"""
import json
import logging
import os

import httpx
from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.errors import MistralError, NoResponseError

from src.extraction.interface import InterfaceLLM
from src.extraction.types import Besoin

load_dotenv()
logger = logging.getLogger(__name__)

MODELE = "mistral-small-latest"

CHAMPS_TEXTE = ("type_evenement", "date_evenement", "ville", "quartier_souhaite")
CHAMPS_ENTIER = ("nombre_invites", "duree_jours", "budget_declare")
CHAMPS_LISTE = ("prestations_souhaitees", "prestations_exclues")

ERREURS_APPEL_MISTRAL = (MistralError, NoResponseError, httpx.HTTPError)

INSTRUCTIONS_EXTRACTION = """Tu extrais les informations d'un besoin événementiel exprimé en langage naturel par un prospect.

Réponds uniquement avec un objet JSON, sans aucun texte avant ou après, respectant exactement ce schéma :
{
  "type_evenement": chaîne ou null,
  "date_evenement": chaîne ou null,
  "ville": chaîne ou null,
  "quartier_souhaite": chaîne ou null,
  "nombre_invites": entier ou null,
  "duree_jours": entier ou null,
  "budget_declare": entier ou null,
  "prestations_souhaitees": liste de chaînes,
  "prestations_exclues": liste de chaînes
}

Règles :
- Un « besoin déjà connu » te sera fourni. Conserve chacun de ses champs si le nouveau message ne lui apporte rien de nouveau.
- N'invente aucune valeur absente du message et du besoin déjà connu.
- Les montants sont des entiers, sans devise ni séparateur de milliers.
- N'écris strictement aucun texte en dehors de cet objet JSON."""

INSTRUCTIONS_REFORMULATION = (
    "Tu reformules le contenu reçu en français naturel, pour un prospect. "
    "Ne change pas le sens, n'ajoute aucune information, ne pose aucune question supplémentaire."
)


class ExtracteurMistral(InterfaceLLM):
    """Implémentation réelle de InterfaceLLM, via l'API Mistral AI"""

    def __init__(self) -> None:
        cle_api = os.getenv("MISTRAL_API_KEY")
        if not cle_api or not cle_api.strip():
            raise RuntimeError("MISTRAL_API_KEY manquante ou vide : vérifie le fichier .env")
        self._client = Mistral(api_key=cle_api)

    def extraire_besoin(self, message: str, besoin_actuel: Besoin) -> Besoin:
        """Demande au modèle le besoin mis à jour ; renvoie le besoin actuel si l'appel ou le JSON échoue"""
        contenu_utilisateur = (
            f"Besoin déjà connu : {json.dumps(_besoin_vers_dict(besoin_actuel), ensure_ascii=False)}\n"
            f"Nouveau message du prospect : {message}"
        )
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
            logger.error("Appel Mistral échoué lors de l'extraction du besoin : %s", erreur)
            return besoin_actuel

        contenu_brut = reponse.choices[0].message.content
        besoin_extrait = _parser_besoin(contenu_brut)
        if besoin_extrait is None:
            logger.error(
                "Réponse Mistral invalide lors de l'extraction du besoin, contenu reçu : %r", contenu_brut
            )
            return besoin_actuel
        return besoin_extrait

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
        return contenu_reformule


def _besoin_vers_dict(besoin: Besoin) -> dict:
    """Sérialise le besoin actuel pour l'inclure dans le prompt d'extraction"""
    return {
        "type_evenement": besoin.type_evenement,
        "date_evenement": besoin.date_evenement,
        "ville": besoin.ville,
        "quartier_souhaite": besoin.quartier_souhaite,
        "nombre_invites": besoin.nombre_invites,
        "duree_jours": besoin.duree_jours,
        "budget_declare": besoin.budget_declare,
        "prestations_souhaitees": list(besoin.prestations_souhaitees),
        "prestations_exclues": list(besoin.prestations_exclues),
    }


def _parser_besoin(contenu_brut: object) -> Besoin | None:
    """Valide le JSON renvoyé par le modèle et le convertit en Besoin, ou None s'il est invalide"""
    if not isinstance(contenu_brut, str):
        return None
    try:
        donnees = json.loads(contenu_brut)
    except json.JSONDecodeError:
        return None
    if not isinstance(donnees, dict):
        return None
    if not all(_est_texte_ou_absent(donnees.get(champ)) for champ in CHAMPS_TEXTE):
        return None
    if not all(_est_entier_ou_absent(donnees.get(champ)) for champ in CHAMPS_ENTIER):
        return None
    if not all(_est_liste_de_textes_ou_absente(donnees.get(champ)) for champ in CHAMPS_LISTE):
        return None

    return Besoin(
        type_evenement=donnees.get("type_evenement"),
        date_evenement=donnees.get("date_evenement"),
        ville=donnees.get("ville"),
        quartier_souhaite=donnees.get("quartier_souhaite"),
        nombre_invites=donnees.get("nombre_invites"),
        duree_jours=donnees.get("duree_jours"),
        budget_declare=donnees.get("budget_declare"),
        prestations_souhaitees=tuple(donnees.get("prestations_souhaitees") or ()),
        prestations_exclues=tuple(donnees.get("prestations_exclues") or ()),
    )


def _est_texte_ou_absent(valeur: object) -> bool:
    return valeur is None or isinstance(valeur, str)


def _est_entier_ou_absent(valeur: object) -> bool:
    return valeur is None or (isinstance(valeur, int) and not isinstance(valeur, bool))


def _est_liste_de_textes_ou_absente(valeur: object) -> bool:
    if valeur is None:
        return True
    return isinstance(valeur, list) and all(isinstance(item, str) for item in valeur)
