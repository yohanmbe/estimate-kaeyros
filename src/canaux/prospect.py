"""Enregistrement du prospect en base à partir de ses coordonnées (voir D26)"""
from sqlalchemy.orm import Session

from src.canaux.types import ProspectContexte
from src.db.models import Prospect


def enregistrer_prospect(
    session: Session,
    tenant_id: str,
    nom: str,
    telephone: str,
    email: str | None,
    consentement_contact: bool,
) -> ProspectContexte:
    """Crée le prospect en base et renvoie son contexte détaché de la session.

    Pas de déduplication (D26) : chaque conversation crée une nouvelle ligne,
    même pour un téléphone déjà vu. Pas de validation de format ici, la base
    n'impose que nom et téléphone non vides ; c'est au formulaire de vérifier
    des champs non vides avant d'appeler cette fonction.
    """
    prospect = Prospect(
        tenant_id=tenant_id,
        nom=nom,
        telephone=telephone,
        email=email,
        consentement_contact=consentement_contact,
    )
    session.add(prospect)
    # Le flush attribue l'identifiant, et le contexte est construit avant le
    # commit : un objet périmé par le commit serait relu par une requête sur sa
    # seule clé primaire, sans filtre tenant_id (voir tests/conftest.py).
    session.flush()
    contexte = ProspectContexte(
        id=prospect.id,
        nom=prospect.nom,
        telephone=prospect.telephone,
        email=prospect.email,
        consentement_contact=prospect.consentement_contact,
    )
    session.commit()
    return contexte
