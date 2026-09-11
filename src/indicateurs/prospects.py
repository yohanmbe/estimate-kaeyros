"""Indicateurs calculés sur la table prospect : nombre de prospects identifiés
et taux de consentement au recontact.

Distincts des quatre indicateurs de D19 (demande, devis), et volontairement pas
des indicateurs de conversion commerciale : ni l'un ni l'autre ne dit ce qu'une
demande devient après l'estimation. Le nombre de prospects et le taux de
consentement sont des faits que le produit connaît dès la création du
prospect (voir DONNEES.md, table prospect).
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Prospect
from src.indicateurs.types import Periode


def compter_prospects(session: Session, tenant_id: str, periode: Periode) -> int:
    """Nombre de prospects identifiés (nouveaux ou reconnus) sur la période.

    Un prospect déjà connu du tenant (même téléphone) qui revient ne pose pas
    de nouvelle date_creation (voir D47, déduplication par téléphone) : ce
    compte peut donc être inférieur à compter_demandes sur la même période
    dès qu'un même prospect ouvre plusieurs demandes.
    """
    return session.scalar(
        select(func.count(Prospect.id)).where(
            Prospect.tenant_id == tenant_id,
            Prospect.date_creation >= periode.debut,
            Prospect.date_creation <= periode.fin,
        )
    )


def calculer_taux_consentement_contact(session: Session, tenant_id: str, periode: Periode) -> int:
    """Pourcentage de prospects de la période ayant consenti à être recontactés.

    0 si le tenant n'a reçu aucun prospect sur la période. Arrondi au pourcent le
    plus proche par arithmétique entière, sans flottant.
    """
    nombre_prospects = session.scalar(
        select(func.count(Prospect.id)).where(
            Prospect.tenant_id == tenant_id,
            Prospect.date_creation >= periode.debut,
            Prospect.date_creation <= periode.fin,
        )
    )
    if not nombre_prospects:
        return 0
    nombre_consentants = session.scalar(
        select(func.count(Prospect.id)).where(
            Prospect.tenant_id == tenant_id,
            Prospect.date_creation >= periode.debut,
            Prospect.date_creation <= periode.fin,
            Prospect.consentement_contact.is_(True),
        )
    )
    return (nombre_consentants * 100 + nombre_prospects // 2) // nombre_prospects
