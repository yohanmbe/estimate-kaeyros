"""Résultat de la résolution du tenant à partir du slug de l'URL (voir tenant.py)"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TenantContexte:
    """Sous-ensemble du tenant utile au canal, détaché de la session SQLAlchemy"""

    id: str
    nom: str
    slug: str
    logo: str | None = None


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
