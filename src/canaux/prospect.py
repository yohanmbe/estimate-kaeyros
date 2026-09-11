"""Enregistrement du prospect en base à partir de ses coordonnées (voir D26, D47)"""
from sqlalchemy import select
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
    """Retrouve le prospect par (tenant_id, téléphone), ou le crée (voir D47).

    Un même téléphone déjà vu pour ce tenant renvoie la fiche existante sans
    la modifier : nom, email et consentement_contact restent ceux de la
    première visite, jamais réécrits par une visite suivante — même logique
    que le mot de passe d'un gestionnaire, jamais réécrit par un second
    passage du seed (voir src/catalogue/provisionnement.py). Pas de
    validation de format ici, la base n'impose que nom et téléphone non
    vides ; c'est au formulaire de vérifier des champs non vides avant
    d'appeler cette fonction.
    """
    prospect = session.scalar(
        select(Prospect).where(Prospect.tenant_id == tenant_id, Prospect.telephone == telephone)
    )
    if prospect is None:
        prospect = Prospect(
            tenant_id=tenant_id,
            nom=nom,
            telephone=telephone,
            email=email,
            consentement_contact=consentement_contact,
        )
        session.add(prospect)
        # Le flush attribue l'identifiant, et le contexte est construit avant
        # le commit : un objet périmé par le commit serait relu par une
        # requête sur sa seule clé primaire, sans filtre tenant_id (voir
        # tests/conftest.py).
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
