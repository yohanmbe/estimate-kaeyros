"""Indicateurs calculés sur la table devis, voir D19 : montant total et montant moyen"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Devis
from src.indicateurs.types import Periode


def calculer_montant_total(session: Session, tenant_id: str, periode: Periode) -> int:
    """Somme des totaux des devis émis sur la période, 0 si aucun devis émis"""
    total = session.scalar(
        select(func.sum(Devis.total)).where(
            Devis.tenant_id == tenant_id,
            Devis.date_emission >= periode.debut,
            Devis.date_emission <= periode.fin,
        )
    )
    return total or 0


def calculer_montant_moyen(session: Session, tenant_id: str, periode: Periode) -> int:
    """Montant moyen d'un devis émis sur la période, 0 si aucun devis émis.

    Arrondi au franc le plus proche par arithmétique entière : le FCFA n'a pas
    de sous-unité et un flottant n'a rien à faire dans un calcul d'argent
    (voir CLAUDE.md, Conventions d'argent).
    """
    total = calculer_montant_total(session, tenant_id, periode)
    nombre_devis = session.scalar(
        select(func.count(Devis.id)).where(
            Devis.tenant_id == tenant_id,
            Devis.date_emission >= periode.debut,
            Devis.date_emission <= periode.fin,
        )
    )
    if not nombre_devis:
        return 0
    return (total + nombre_devis // 2) // nombre_devis
