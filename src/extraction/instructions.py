"""Consignes envoyées au modèle, communes à tous les fournisseurs

Un seul exemplaire de ces consignes : elles étaient auparavant recopiées mot
pour mot dans chaque implémentation, si bien qu'une correction n'était
appliquée qu'à moitié selon le fournisseur configuré.
"""
import json
from datetime import date

from src.extraction.types import Besoin
from src.extraction.villes import VILLES_CAMEROUN
from src.presentation.dates import JOURS_SEMAINE

INSTRUCTIONS_EXTRACTION = f"""Tu extrais les informations d'un besoin événementiel exprimé en langage naturel par un prospect.

Réponds uniquement avec un objet JSON, sans aucun texte avant ou après, respectant exactement ce schéma :
{{
  "type_evenement": chaîne ou null,
  "date_evenement": chaîne ou null,
  "dates_possibles": liste de chaînes,
  "ville": chaîne ou null,
  "quartier_souhaite": chaîne ou null,
  "nombre_invites": entier ou null,
  "duree_jours": entier ou null,
  "budget_declare": entier ou null,
  "prestations_souhaitees": liste de chaînes,
  "prestations_exclues": liste de chaînes,
  "champs_a_confirmer": liste de chaînes
}}

Règles :
- Un « besoin déjà connu » te sera fourni. Conserve chacun de ses champs si le nouveau message ne lui apporte rien de nouveau.
- N'invente aucune valeur absente du message et du besoin déjà connu.
- Si le nouveau message est un nombre seul (par exemple « 1 » ou « 300 »), sans autre précision, et qu'un seul des deux champs nombre_invites ou duree_jours est encore vide dans le besoin déjà connu, attribue ce nombre à ce champ. budget_declare n'entre pas dans cette règle : son absence est l'état normal tant que le prospect n'a rien dit de son budget, elle ne crée aucune ambiguïté. Si nombre_invites et duree_jours sont tous deux vides, n'en devine aucun.

Type d'événement :
- type_evenement vaut "mariage" dès que le message parle de mariage, même sans employer ce mot : dot, dote, doté, coutumier, mariage civil, mariage religieux, bénédiction nuptiale, noces, réception de mariage, cérémonie de mariage, union, épouser, se marier. Écris toujours "mariage" en un seul mot, en minuscules.
- Un autre type d'événement (anniversaire, baptême, séminaire...) s'écrit aussi en minuscules, tel que le prospect le nomme.

Ville et quartier :
- ville désigne une ville. Voici les villes du Cameroun que tu dois savoir reconnaître, avec leur graphie exacte à recopier : {", ".join(VILLES_CAMEROUN)}.
- Corrige la graphie du prospect vers celle de cette liste : « yaounde », « YAOUNDÉ » et « Yaoundé » désignent la même ville, à écrire « Yaoundé ».
- Une ville hors de cette liste reste valable : recopie-la telle que le prospect l'écrit.
- quartier_souhaite désigne un quartier à l'intérieur d'une ville (Bastos, Mvan, Odza, Essos, Tsinga, Akwa, Bonapriso sont des quartiers, pas des villes). Si le prospect ne cite qu'un nom de quartier sans nommer la ville, mets-le dans quartier_souhaite et laisse ville à null plutôt que de les confondre.

Date :
- date_evenement s'écrit toujours au format AAAA-MM-JJ. La date du jour te sera fournie : sers-t'en pour résoudre toute expression relative.
- Si l'expression désigne un seul jour (« samedi prochain », « le 12 juillet », « demain »), écris la date correspondante dans date_evenement et ajoute "date_evenement" à champs_a_confirmer.
- Si l'expression couvre plusieurs jours possibles (« ce weekend », « début décembre », « la semaine prochaine »), laisse date_evenement à null et écris les dates concrètes candidates dans dates_possibles, au format AAAA-MM-JJ. Pour un weekend, ce sont le samedi et le dimanche concernés. N'en choisis aucune toi-même : c'est au prospect de trancher.
- Une année non précisée est celle qui rend la date future par rapport à la date du jour.
- Quand l'expression nomme un jour de la semaine (« le dernier samedi de décembre », « samedi prochain », « le vendredi 12 »), la date que tu écris DOIT tomber ce jour-là. Calcule le jour de la semaine de ta date avant de répondre : si elle ne tombe pas le bon jour, corrige-la. « Le dernier samedi de décembre 2026 » est le 26 décembre 2026, pas le 31 qui est un jeudi.
- Si le prospect conteste une valeur que tu lui as proposée (« non », « pas le jeudi », « plutôt samedi », « non samedi »), corrige cette valeur en tenant compte de ce qu'il vient de dire. Ne répète jamais à l'identique une valeur qu'il vient de refuser.

Durée :
- duree_jours est un entier. Comprends les durées écrites en toutes lettres : « un jour », « une journée », « la journée », « une seule journée », « la journée entière » valent 1 ; « deux jours », « le weekend », « samedi et dimanche » valent 2 ; « trois jours » vaut 3.
- Si le prospect donne une plage de dates explicite avec ses deux bornes (par exemple « du 12 au 14 décembre »), calcule duree_jours comme le nombre de jours couverts, bornes incluses (12, 13, 14 décembre = 3 jours). N'applique cette règle que si les deux bornes sont explicitement données. Une date seule, même précise, ne permet jamais de déduire duree_jours : il reste vide tant que le prospect ne l'a pas dit.

Ce dont tu n'es pas sûr :
- champs_a_confirmer liste les noms des champs que tu as **déduits** au lieu de les lire : une date relative résolue, un type d'événement compris à partir d'un mot indirect, une valeur dont tu doutes.
- Ne signale que ce que tu déduis du nouveau message. Un champ repris tel quel du besoin déjà connu n'est pas à confirmer.
- Ne pose jamais de question toi-même : contente-toi de signaler le champ, quelqu'un d'autre s'en chargera.

- Les montants sont des entiers, sans devise ni séparateur de milliers.
- N'écris strictement aucun texte en dehors de cet objet JSON."""

INSTRUCTIONS_REFORMULATION = (
    "Tu reformules le contenu reçu en français naturel, pour un prospect. "
    "Ne change pas le sens, n'ajoute aucune information, ne pose aucune question supplémentaire. "
    "Ne commence pas systématiquement par une formule du type « pour préparer votre estimation » "
    "ou « afin de vous fournir une estimation » : va droit au but. "
    "N'invente jamais de date, de durée, de quantité ou de montant absent du contenu reçu : si le "
    "contenu dit qu'une information manque, ta reformulation doit dire qu'elle manque, jamais "
    "répondre à sa place avec une valeur inventée."
)


def construire_contenu_utilisateur(
    message: str, besoin_actuel: Besoin, aujourd_hui: date | None = None
) -> str:
    """Assemble le message envoyé au modèle : date du jour, besoin connu, nouveau message.

    La date du jour est indispensable : sans elle, « ce weekend » ou « samedi
    prochain » ne désignent rien de calculable. Elle est injectable pour que
    les tests ne dépendent pas du jour où ils tournent.
    """
    jour = aujourd_hui or date.today()
    return (
        f"Date du jour : {jour.isoformat()} ({JOURS_SEMAINE[jour.weekday()]})\n"
        f"Besoin déjà connu : {json.dumps(besoin_vers_dict(besoin_actuel), ensure_ascii=False)}\n"
        f"Nouveau message du prospect : {message}"
    )


def besoin_vers_dict(besoin: Besoin) -> dict:
    """Sérialise le besoin actuel pour l'inclure dans le prompt d'extraction.

    Les champs pilotés par le canal — ressources choisies, hypothèses déjà
    confirmées — n'y figurent pas : ils relèvent de la conduite de la
    conversation, pas de la lecture du message (voir D01, D04).
    """
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
