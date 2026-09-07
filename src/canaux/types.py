"""Contextes que les canaux manipulent, tous détachés de la session SQLAlchemy.

Un objet SQLAlchemy vivant ne survit pas à un rerun Streamlit : il lèverait
DetachedInstanceError au tour suivant. Les canaux ne voient donc que ces
dataclasses figées.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class TenantContexte:
    """Sous-ensemble du tenant utile au canal, détaché de la session SQLAlchemy"""

    id: str
    nom: str
    slug: str
    logo: str | None = None
    coordonnees: str | None = None


@dataclass(frozen=True)
class TenantResolu:
    tenant: TenantContexte


@dataclass(frozen=True)
class TenantIndisponible:
    """Aucune conversation ne doit démarrer : pas de tenant par défaut en repli"""

    raison: Literal["slug_absent", "slug_inconnu", "tenant_inactif"]


ResolutionTenant = TenantResolu | TenantIndisponible


@dataclass(frozen=True)
class ProspectContexte:
    """Sous-ensemble du prospect utile au canal, détaché de la session SQLAlchemy"""

    id: str
    nom: str
    telephone: str
    email: str | None
    consentement_contact: bool


@dataclass(frozen=True)
class DemandeOuverte:
    """La demande ouverte pour la conversation en cours (voir canaux/demande.py)"""

    id: str
    etat: str


@dataclass(frozen=True)
class DevisEmis:
    """Reçu d'un devis figé en base : ce qui a été écrit, jamais un recalcul (D11)"""

    id: str
    total: int
    devise: str
    date_emission: datetime
