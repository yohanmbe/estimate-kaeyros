"""Résultat de la tentative de connexion d'un gestionnaire (voir connexion.py)"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UtilisateurContexte:
    """Sous-ensemble de l'utilisateur utile au tableau de bord, détaché de la session SQLAlchemy"""

    id: str
    tenant_id: str
    email: str
    nom: str


@dataclass(frozen=True)
class ConnexionReussie:
    utilisateur: UtilisateurContexte


@dataclass(frozen=True)
class ConnexionEchouee:
    """Une seule raison est montrée au gestionnaire (voir dashboard/connexion.py) :
    jamais de distinction visible entre email inconnu et mot de passe erroné,
    pour ne pas révéler quels emails ont un compte."""

    raison: Literal["identifiants_invalides", "compte_inactif"]


ResolutionConnexion = ConnexionReussie | ConnexionEchouee
