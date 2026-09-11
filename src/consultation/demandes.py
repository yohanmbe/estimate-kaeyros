"""Lecture des demandes reçues, pour les écrans du gestionnaire.

Symétrique de src/canaux/demande.py, qui écrit : ici on ne fait que lire, et
aucun montant n'est recalculé. Les totaux affichés sortent des lignes figées à
l'émission (D11), jamais d'un nouveau passage par le moteur.

Chaque requête filtre sur tenant_id, y compris celles qui vont chercher le
prospect ou les devis rattachés : la clé étrangère ne garantit pas à elle seule
qu'une ligne liée appartient au même locataire, seul le filtre le fait
(voir CLAUDE.md, Multi-locataires).
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.consultation.types import (
    DetailDemande,
    DevisConsulte,
    LigneDevisFigee,
    LigneListeDemande,
    ProspectDeLaDemande,
)
from src.db.models import Demande, Devis, Prospect
from src.indicateurs.types import Periode


def lister_demandes(
    session: Session,
    tenant_id: str,
    periode: Periode,
    etat: str | None = None,
    limite: int | None = None,
) -> list[LigneListeDemande]:
    """Demandes du tenant sur la période, de la plus récente à la plus ancienne"""
    conditions = [
        Demande.tenant_id == tenant_id,
        Demande.date_creation >= periode.debut,
        Demande.date_creation <= periode.fin,
    ]
    if etat is not None:
        conditions.append(Demande.etat == etat)

    requete = select(Demande).where(*conditions).order_by(Demande.date_creation.desc())
    if limite is not None:
        requete = requete.limit(limite)

    demandes = list(session.scalars(requete))
    identifiants = [demande.id for demande in demandes]
    prospects = _prospects_du_tenant(session, tenant_id, demandes)
    derniers_devis = _dernier_devis_par_demande(session, tenant_id, identifiants)
    return [
        _resumer(demande, prospects.get(demande.prospect_id), derniers_devis.get(demande.id))
        for demande in demandes
    ]


def lister_demandes_du_prospect(
    session: Session, tenant_id: str, prospect_id: str
) -> list[LigneListeDemande]:
    """Toutes les demandes d'un prospect, de la plus récente à la plus ancienne.

    Sans borne de période, contrairement à lister_demandes : la fiche d'un
    prospect porte son historique entier, c'est ce qu'on vient y chercher.
    """
    demandes = list(
        session.scalars(
            select(Demande)
            .where(Demande.tenant_id == tenant_id, Demande.prospect_id == prospect_id)
            .order_by(Demande.date_creation.desc())
        )
    )
    identifiants = [demande.id for demande in demandes]
    prospects = _prospects_du_tenant(session, tenant_id, demandes)
    derniers_devis = _dernier_devis_par_demande(session, tenant_id, identifiants)
    return [
        _resumer(demande, prospects.get(demande.prospect_id), derniers_devis.get(demande.id))
        for demande in demandes
    ]


def consulter_demande(session: Session, tenant_id: str, demande_id: str) -> DetailDemande | None:
    """Détail d'une demande du tenant, None si elle ne lui appartient pas.

    Le filtre porte sur l'identifiant ET le tenant, jamais « charger puis
    vérifier » : les identifiants de demandes circulent dans les clés de
    widgets, connaître celui d'une autre entreprise ne doit donner accès à rien.
    """
    demande = session.scalar(
        select(Demande).where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
    )
    if demande is None:
        return None

    prospects = _prospects_du_tenant(session, tenant_id, [demande])
    devis = [
        _convertir_devis(ligne)
        for ligne in session.scalars(
            select(Devis)
            .where(Devis.tenant_id == tenant_id, Devis.demande_id == demande.id)
            .order_by(Devis.date_emission.desc())
        )
    ]
    resume = _resumer(
        demande,
        prospects.get(demande.prospect_id),
        devis[0] if devis else None,
    )
    return DetailDemande(
        resume=resume,
        besoin=demande.besoin,
        devis=tuple(devis),
        besoins_hors_catalogue=demande.besoins_hors_catalogue,
        commentaire=demande.commentaire,
    )


def compter_demandes_du_tenant(session: Session, tenant_id: str) -> int:
    """Nombre total de demandes du tenant, toutes périodes : sert au repère de navigation"""
    return session.scalar(
        select(func.count(Demande.id)).where(Demande.tenant_id == tenant_id)
    )


def _prospects_du_tenant(
    session: Session, tenant_id: str, demandes: list[Demande]
) -> dict[str, ProspectDeLaDemande]:
    """Prospects du tenant rattachés à ces demandes, indexés par identifiant.

    Requête explicite plutôt que la relation SQLAlchemy : un chargement
    paresseux irait chercher le prospect par sa seule clé étrangère, sans
    filtrer sur le tenant. Un prospect d'une autre entreprise reste donc
    introuvable ici, et la demande s'affiche sans coordonnées.
    """
    identifiants = {demande.prospect_id for demande in demandes if demande.prospect_id}
    if not identifiants:
        return {}
    prospects = session.scalars(
        select(Prospect).where(
            Prospect.tenant_id == tenant_id, Prospect.id.in_(identifiants)
        )
    )
    nombre_demandes = _compter_demandes_par_prospect(session, tenant_id, identifiants)
    return {
        prospect.id: ProspectDeLaDemande(
            id=prospect.id,
            nom=prospect.nom,
            telephone=prospect.telephone,
            email=prospect.email,
            consentement_contact=prospect.consentement_contact,
            nombre_demandes=nombre_demandes.get(prospect.id, 0),
        )
        for prospect in prospects
    }


def _compter_demandes_par_prospect(
    session: Session, tenant_id: str, identifiants: set[str]
) -> dict[str, int]:
    """Nombre de demandes de chaque prospect, toutes périodes confondues (voir D47).

    Pas limité à la période affichée : un prospect qui revient après
    plusieurs mois doit rester reconnu comme tel sur le détail d'une demande.
    """
    lignes = session.execute(
        select(Demande.prospect_id, func.count(Demande.id))
        .where(Demande.tenant_id == tenant_id, Demande.prospect_id.in_(identifiants))
        .group_by(Demande.prospect_id)
    )
    # dict(lignes) traiterait le Result comme un mapping (il porte .keys())
    # plutôt que comme un itérable de couples : .all() force la liste de lignes.
    return dict(lignes.all())


def _dernier_devis_par_demande(
    session: Session, tenant_id: str, identifiants: list[str]
) -> dict[str, DevisConsulte]:
    """Devis le plus récent de chaque demande, celui que la liste doit montrer"""
    if not identifiants:
        return {}
    devis_du_plus_ancien_au_plus_recent = session.scalars(
        select(Devis)
        .where(Devis.tenant_id == tenant_id, Devis.demande_id.in_(identifiants))
        .order_by(Devis.date_emission)
    )
    return {
        devis.demande_id: _convertir_devis(devis)
        for devis in devis_du_plus_ancien_au_plus_recent
    }


def _convertir_devis(devis: Devis) -> DevisConsulte:
    """Traduit une ligne de la table devis vers la vue du gestionnaire"""
    return DevisConsulte(
        id=devis.id,
        total=devis.total,
        devise=devis.devise,
        date_emission=devis.date_emission,
        lignes=tuple(_convertir_ligne(ligne) for ligne in devis.lignes),
    )


def _convertir_ligne(ligne: dict) -> LigneDevisFigee:
    """Traduit une ligne figée du JSON du devis, sans jamais recalculer son montant"""
    return LigneDevisFigee(
        designation=ligne["designation"],
        quantite=ligne["quantite"],
        prix_unitaire=ligne["prix_unitaire"],
        montant=ligne["montant"],
    )


def _resumer(
    demande: Demande,
    prospect: ProspectDeLaDemande | None,
    dernier_devis: DevisConsulte | None,
) -> LigneListeDemande:
    """Assemble la ligne de liste à partir de la demande, de son prospect et de son devis"""
    besoin = demande.besoin or {}
    return LigneListeDemande(
        id=demande.id,
        date_creation=demande.date_creation,
        etat=demande.etat,
        canal=demande.canal,
        type_evenement=besoin.get("type_evenement"),
        date_evenement=besoin.get("date_evenement"),
        ville=besoin.get("ville"),
        quartier_souhaite=besoin.get("quartier_souhaite"),
        nombre_invites=besoin.get("nombre_invites"),
        prospect=prospect,
        total_dernier_devis=dernier_devis.total if dernier_devis else None,
        devise=dernier_devis.devise if dernier_devis else None,
    )
