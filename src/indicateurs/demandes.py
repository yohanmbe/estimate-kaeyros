"""Indicateurs calculés sur la table demande, voir D19 : nombre de demandes et
répartition par tranche d'invités.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Demande
from src.indicateurs.types import TRANCHES_INVITES, EffectifTranche, Periode


def compter_demandes(session: Session, tenant_id: str, periode: Periode) -> int:
    """Nombre de demandes reçues par le tenant sur la période"""
    return session.scalar(
        select(func.count(Demande.id)).where(
            Demande.tenant_id == tenant_id,
            Demande.date_creation >= periode.debut,
            Demande.date_creation <= periode.fin,
        )
    )


def repartir_par_tranche_invites(
    session: Session, tenant_id: str, periode: Periode
) -> list[EffectifTranche]:
    """Regroupe les demandes de la période par tranche de nombre d'invités.

    Une demande dont le besoin ne porte pas encore nombre_invites (conversation
    interrompue avant cette information) n'entre dans aucune tranche : la somme
    des tranches peut donc être inférieure à compter_demandes sur la même période.
    """
    demandes = session.scalars(
        select(Demande).where(
            Demande.tenant_id == tenant_id,
            Demande.date_creation >= periode.debut,
            Demande.date_creation <= periode.fin,
        )
    )
    effectifs = {nom: 0 for nom, _, _ in TRANCHES_INVITES}
    for demande in demandes:
        tranche = _trouver_tranche(demande.besoin.get("nombre_invites"))
        if tranche is not None:
            effectifs[tranche] += 1
    return [EffectifTranche(tranche=nom, nombre_demandes=effectifs[nom]) for nom, _, _ in TRANCHES_INVITES]


def _trouver_tranche(nombre_invites: int | None) -> str | None:
    """Nom de la tranche contenant ce nombre d'invités, None si absent ou hors bornes"""
    if nombre_invites is None:
        return None
    for nom, minimum, maximum in TRANCHES_INVITES:
        if nombre_invites >= minimum and (maximum is None or nombre_invites <= maximum):
            return nom
    return None
