"""Vérification des identifiants d'un gestionnaire contre la table utilisateur (voir CLAUDE.md, D18)"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.hachage import verifie_mot_de_passe
from src.auth.types import (
    ConnexionEchouee,
    ConnexionReussie,
    ResolutionConnexion,
    UtilisateurContexte,
)
from src.db.models import Utilisateur


def connecter(session: Session, email: str, mot_de_passe: str) -> ResolutionConnexion:
    """Vérifie l'email et le mot de passe, puis contrôle que le compte est actif.

    Le mot de passe en clair ne sort jamais de cette fonction : ni retourné,
    ni journalisé, même en cas d'échec. Ne committe pas la mise à jour de
    derniere_connexion : à l'appelant de le faire, comme pour provisionner_tenant.
    """
    utilisateur = session.scalar(select(Utilisateur).where(Utilisateur.email == email))
    if utilisateur is None or not verifie_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hache):
        return ConnexionEchouee(raison="identifiants_invalides")
    if not utilisateur.actif:
        return ConnexionEchouee(raison="compte_inactif")

    utilisateur.derniere_connexion = datetime.utcnow()
    return ConnexionReussie(
        utilisateur=UtilisateurContexte(
            id=utilisateur.id,
            tenant_id=utilisateur.tenant_id,
            email=utilisateur.email,
            nom=utilisateur.nom,
        )
    )
