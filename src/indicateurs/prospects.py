"""Indicateur calculé sur la table prospect : taux de consentement au recontact.

Distinct des quatre indicateurs de D19 (demande, devis), et volontairement pas un
indicateur de conversion commerciale : celui-ci ne dit rien de ce qu'une demande
devient après l'estimation, seulement la part des prospects ayant accepté d'être
recontactés au moment où ils l'ont formulée, un fait que le produit connaît dès
la création du prospect (voir DONNEES.md, table prospect, champ
consentement_contact).
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Prospect
from src.indicateurs.types import Periode


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
