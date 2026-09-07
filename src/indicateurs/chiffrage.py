"""Indicateur croisant demande et devis : taux de demandes chiffrées.

Distinct des quatre indicateurs de D19 et volontairement pas un indicateur de
conversion commerciale : chiffrer un devis est un acte du produit lui-même,
connu avec certitude via la table devis (voir D11, un devis émis y est figé),
à la différence d'une vente dont le produit n'a aucune trace après l'estimation
(voir D08). Ça reste une mesure du produit sur lui-même, pas une estimation de
ce que le prospect en fait ensuite.
"""
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from src.db.models import Demande, Devis
from src.indicateurs.types import Periode


def calculer_taux_demandes_chiffrees(session: Session, tenant_id: str, periode: Periode) -> int:
    """Pourcentage de demandes de la période pour lesquelles un devis a été émis.

    0 si le tenant n'a reçu aucune demande sur la période. Arrondi au pourcent
    le plus proche par arithmétique entière, sans flottant.
    """
    nombre_demandes = session.scalar(
        select(func.count(Demande.id)).where(
            Demande.tenant_id == tenant_id,
            Demande.date_creation >= periode.debut,
            Demande.date_creation <= periode.fin,
        )
    )
    if not nombre_demandes:
        return 0
    nombre_chiffrees = session.scalar(
        select(func.count(Demande.id)).where(
            Demande.tenant_id == tenant_id,
            Demande.date_creation >= periode.debut,
            Demande.date_creation <= periode.fin,
            # Le devis est filtré sur le tenant lui aussi, pas seulement la
            # demande à laquelle il se rattache : la clé étrangère ne garantit
            # pas qu'une ligne liée appartient au même locataire.
            exists().where(Devis.demande_id == Demande.id, Devis.tenant_id == tenant_id),
        )
    )
    return (nombre_chiffrees * 100 + nombre_demandes // 2) // nombre_demandes
