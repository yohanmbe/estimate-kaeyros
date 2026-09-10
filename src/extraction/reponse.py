"""Validation et normalisation de la réponse JSON du modèle

Commun à tous les fournisseurs. Le modèle est faillible : ce module refuse
une réponse mal formée, et rattrape ce qui peut l'être sans rien inventer.
"""
import json
import re
from datetime import date

from src.extraction.types import Besoin
from src.extraction.villes import normaliser_ville
from src.presentation.dates import JOURS_SEMAINE

CHAMP_DATE = "date_evenement"

CHAMPS_TEXTE = ("type_evenement", "date_evenement", "ville", "quartier_souhaite")
CHAMPS_ENTIER = ("nombre_invites", "duree_jours", "budget_declare")
CHAMPS_LISTE = (
    "prestations_souhaitees",
    "prestations_exclues",
    "dates_possibles",
    "champs_a_confirmer",
)

# Les seuls champs qu'il a un sens de faire confirmer au prospect : ceux qu'il
# a lui-même exprimés. Un nom de champ inventé par le modèle est ignoré.
CHAMPS_CONFIRMABLES = CHAMPS_TEXTE + CHAMPS_ENTIER


def parser_besoin(contenu_brut: object, message: str = "") -> Besoin | None:
    """Valide le JSON renvoyé par le modèle et le convertit en Besoin, ou None s'il est invalide.

    Le message du prospect sert de garde-fou : lui seul permet de vérifier
    que la date produite tombe bien le jour de la semaine qu'il a nommé.
    """
    donnees = _charger_objet_json(contenu_brut)
    if donnees is None:
        return None
    if not all(_est_texte_ou_absent(donnees.get(champ)) for champ in CHAMPS_TEXTE):
        return None
    if not all(_est_entier_ou_absent(donnees.get(champ)) for champ in CHAMPS_ENTIER):
        return None
    if not all(_est_liste_de_textes_ou_absente(donnees.get(champ)) for champ in CHAMPS_LISTE):
        return None

    date_evenement = _nettoyer_texte(donnees.get("date_evenement"))
    date_contredite = _contredit_le_jour_nomme(message, date_evenement)
    return Besoin(
        type_evenement=_nettoyer_texte(donnees.get("type_evenement")),
        date_evenement=None if date_contredite else date_evenement,
        ville=normaliser_ville(donnees.get("ville")),
        quartier_souhaite=_nettoyer_texte(donnees.get("quartier_souhaite")),
        nombre_invites=donnees.get("nombre_invites"),
        duree_jours=donnees.get("duree_jours"),
        budget_declare=donnees.get("budget_declare"),
        prestations_souhaitees=tuple(donnees.get("prestations_souhaitees") or ()),
        prestations_exclues=tuple(donnees.get("prestations_exclues") or ()),
        dates_possibles=tuple(donnees.get("dates_possibles") or ()),
        champs_a_confirmer=(
            ()
            if date_contredite
            else _resoudre_champs_a_confirmer(
                donnees.get("champs_a_confirmer") or (), date_evenement
            )
        ),
        champ_en_correction=CHAMP_DATE if date_contredite else None,
    )


def _contredit_le_jour_nomme(message: str, date_evenement: str | None) -> bool:
    """Vrai si le prospect a nommé un jour de la semaine et que la date n'y tombe pas.

    « Le dernier samedi de décembre » a produit un jeudi, proposé deux fois
    de suite. Plutôt que de montrer une date manifestement fausse, on
    l'écarte et on la redemande : le prospect a été clair, c'est le modèle
    qui a mal lu.

    Un message citant plusieurs jours (« samedi ou dimanche ») n'est pas
    tranchable : on laisse passer plutôt que de choisir à sa place.
    """
    if date_evenement is None or not _est_date_canonique(date_evenement):
        return False
    jours_nommes = _jours_nommes_dans(message)
    if len(jours_nommes) != 1:
        return False
    return JOURS_SEMAINE[date.fromisoformat(date_evenement).weekday()] not in jours_nommes


def _jours_nommes_dans(message: str) -> set[str]:
    """Jours de la semaine cités dans le message, en mot entier"""
    mots = set(re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ]+", message.casefold()))
    return {jour for jour in JOURS_SEMAINE if jour in mots}


def _resoudre_champs_a_confirmer(
    champs_signales: object, date_evenement: str | None
) -> tuple[str, ...]:
    """Retient les champs signalés par le modèle, et ajoute la date si elle est hors format.

    Une date que le modèle n'a pas su écrire au format canonique n'est jamais
    jetée : elle part à confirmer, pour être reformulée au prospect qui la
    corrigera. La perdre en silence reviendrait à la lui redemander comme
    s'il ne l'avait jamais donnée.
    """
    champs = [
        champ for champ in champs_signales if champ in CHAMPS_CONFIRMABLES  # type: ignore[union-attr]
    ]
    if date_evenement is not None and not _est_date_canonique(date_evenement):
        champs.append("date_evenement")
    return tuple(dict.fromkeys(champs))


def _est_date_canonique(valeur: str) -> bool:
    """Vrai si la date est écrite au format AAAA-MM-JJ et désigne un jour réel"""
    try:
        date.fromisoformat(valeur)
    except ValueError:
        return False
    return True


def _charger_objet_json(contenu_brut: object) -> dict | None:
    """Décode le contenu en objet JSON, ou None si ce n'en est pas un"""
    if not isinstance(contenu_brut, str):
        return None
    try:
        donnees = json.loads(contenu_brut)
    except json.JSONDecodeError:
        return None
    return donnees if isinstance(donnees, dict) else None


def _nettoyer_texte(valeur: object) -> str | None:
    """Retire les espaces superflus, et traite un texte vide comme une absence"""
    if not isinstance(valeur, str):
        return None
    nettoye = valeur.strip()
    return nettoye or None


def _est_texte_ou_absent(valeur: object) -> bool:
    return valeur is None or isinstance(valeur, str)


def _est_entier_ou_absent(valeur: object) -> bool:
    return valeur is None or (isinstance(valeur, int) and not isinstance(valeur, bool))


def _est_liste_de_textes_ou_absente(valeur: object) -> bool:
    if valeur is None:
        return True
    return isinstance(valeur, list) and all(isinstance(item, str) for item in valeur)


def contient_un_nombre_invente(source: str, reformule: str) -> bool:
    """Vrai si la reformulation contient un nombre absent de la source, signe d'une invention.

    Le contenu envoyé à reformuler() ne porte jamais de nombre quand il
    signale une information manquante : un nombre qui apparaît dans la
    reformulation vient forcément d'ailleurs, jamais du texte à reformuler.
    """
    nombres_source = set(re.findall(r"\d+", source))
    nombres_reformule = set(re.findall(r"\d+", reformule))
    return bool(nombres_reformule - nombres_source)
