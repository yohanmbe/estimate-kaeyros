"""Lecture des prospects, pour le carnet d'adresses du gestionnaire (voir D49).

Symétrique de src/canaux/prospect.py, qui écrit : ici on ne fait que lire, et
aucune fiche n'est modifiée. Le pendant par la demande est
src/consultation/demandes.py, dont ce module réutilise la lecture des
demandes d'un prospect plutôt que de la refaire.

Chaque requête filtre sur tenant_id, y compris celle qui va compter les
demandes rattachées : la clé étrangère ne garantit pas à elle seule qu'une
ligne liée appartient au même locataire, seul le filtre le fait
(voir CLAUDE.md, Multi-locataires).
"""
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from src.consultation.demandes import lister_demandes_du_prospect
from src.consultation.types import DetailProspect, LigneListeProspect
from src.db.models import Demande, Prospect
from src.indicateurs.types import Periode

# LIKE traite % et _ comme des jokers : sans échappement, chercher « % »
# renverrait tout le carnet. Le caractère d'échappement est déclaré à ilike.
CARACTERE_ECHAPPEMENT = "\\"
JOKERS_LIKE = ("%", "_")


def lister_prospects(
    session: Session,
    tenant_id: str,
    periode: Periode,
    recherche: str | None = None,
    limite: int | None = None,
) -> list[LigneListeProspect]:
    """Prospects du tenant créés sur la période, du plus récent au plus ancien.

    La période porte sur la date de création du prospect, comme
    src/indicateurs/prospects.py::compter_prospects : le nombre affiché sur
    la carte du tableau de bord et le nombre de lignes de cet écran doivent
    toujours dire la même chose. Le tri porte sur la même colonne, pour
    qu'un changement de période ne réordonne pas la liste sur un autre
    critère que celui qui la filtre.
    """
    requete = (
        select(Prospect)
        .where(
            Prospect.tenant_id == tenant_id,
            Prospect.date_creation >= periode.debut,
            Prospect.date_creation <= periode.fin,
        )
        .order_by(Prospect.date_creation.desc())
    )
    requete = _restreindre_a_la_recherche(requete, recherche)
    if limite is not None:
        requete = requete.limit(limite)

    prospects = list(session.scalars(requete))
    activite = _activite_par_prospect(
        session, tenant_id, {prospect.id for prospect in prospects}
    )
    return [_resumer(prospect, *activite.get(prospect.id, (0, None))) for prospect in prospects]


def consulter_prospect(
    session: Session, tenant_id: str, prospect_id: str
) -> DetailProspect | None:
    """Fiche d'un prospect du tenant, None s'il ne lui appartient pas.

    Le filtre porte sur l'identifiant ET le tenant, jamais « charger puis
    vérifier » : les identifiants de prospects circulent dans les clés de
    widgets, connaître celui d'une autre entreprise ne doit donner accès à rien.
    """
    prospect = session.scalar(
        select(Prospect).where(Prospect.id == prospect_id, Prospect.tenant_id == tenant_id)
    )
    if prospect is None:
        return None

    demandes = lister_demandes_du_prospect(session, tenant_id, prospect.id)
    # Le résumé se déduit des demandes qu'on vient de lire plutôt que d'une
    # seconde requête d'agrégat : la fiche et son en-tête ne peuvent alors
    # pas se contredire.
    date_derniere = demandes[0].date_creation if demandes else None
    return DetailProspect(
        resume=_resumer(prospect, len(demandes), date_derniere),
        demandes=tuple(demandes),
    )


def _restreindre_a_la_recherche(requete: Select, recherche: str | None) -> Select:
    """Ajoute le filtre nom ou téléphone, si un terme non vide a été saisi.

    Le motif du téléphone est le terme débarrassé de ses espaces : le
    gestionnaire recopie « 699 00 11 22 » depuis son écran d'appel alors que
    la base stocke le numéro d'un seul tenant.
    """
    terme = (recherche or "").strip()
    if not terme:
        return requete
    return requete.where(
        or_(
            Prospect.nom.ilike(_motif(terme), escape=CARACTERE_ECHAPPEMENT),
            Prospect.telephone.ilike(
                _motif(terme.replace(" ", "")), escape=CARACTERE_ECHAPPEMENT
            ),
        )
    )


def _motif(terme: str) -> str:
    """Terme cherché n'importe où dans la valeur, ses jokers neutralisés"""
    echappe = terme.replace(CARACTERE_ECHAPPEMENT, CARACTERE_ECHAPPEMENT * 2)
    for joker in JOKERS_LIKE:
        echappe = echappe.replace(joker, CARACTERE_ECHAPPEMENT + joker)
    return f"%{echappe}%"


def _activite_par_prospect(
    session: Session, tenant_id: str, identifiants: set[str]
) -> dict[str, tuple[int, datetime]]:
    """Nombre de demandes et date de la dernière, pour chacun de ces prospects.

    Une seule requête groupée plutôt qu'une par ligne affichée. Elle ne
    borne pas par période, à dessein : combien de fois un prospect est revenu
    est un fait sur lui (voir D47), pas sur la période que la liste montre.
    """
    if not identifiants:
        return {}
    lignes = session.execute(
        select(Demande.prospect_id, func.count(Demande.id), func.max(Demande.date_creation))
        .where(Demande.tenant_id == tenant_id, Demande.prospect_id.in_(identifiants))
        .group_by(Demande.prospect_id)
    )
    return {
        prospect_id: (nombre, derniere) for prospect_id, nombre, derniere in lignes.all()
    }


def _resumer(
    prospect: Prospect, nombre_demandes: int, date_derniere_demande: datetime | None
) -> LigneListeProspect:
    """Assemble la ligne de liste à partir de la fiche et de son activité"""
    return LigneListeProspect(
        id=prospect.id,
        nom=prospect.nom,
        telephone=prospect.telephone,
        email=prospect.email,
        consentement_contact=prospect.consentement_contact,
        date_creation=prospect.date_creation,
        nombre_demandes=nombre_demandes,
        date_derniere_demande=date_derniere_demande,
    )
