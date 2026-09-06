"""Résolution du tenant du prospect à partir du slug de l'URL (voir CLAUDE.md, Multi-locataires)"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.canaux.types import ResolutionTenant, TenantContexte, TenantIndisponible, TenantResolu
from src.db.models import Tenant


def extraire_slug_depuis_url() -> str | None:
    """Lit le slug dans les paramètres de l'URL Streamlit (?slug=...), absent si non fourni"""
    import streamlit as st

    return st.query_params.get("slug")


def resoudre_tenant(session: Session, slug: str | None) -> ResolutionTenant:
    """Résout le tenant à partir d'un slug, sans jamais se rabattre sur un tenant par défaut.

    Trois cas font échouer la résolution : slug absent (ou vide), slug ne
    correspondant à aucun tenant, ou tenant existant mais désactivé
    (actif=false). L'appelant doit traiter TenantIndisponible et ne pas
    démarrer la conversation, plutôt que de planter ou d'inventer un tenant.
    """
    if not slug:
        return TenantIndisponible(raison="slug_absent")

    tenant = session.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        return TenantIndisponible(raison="slug_inconnu")
    if not tenant.actif:
        return TenantIndisponible(raison="tenant_inactif")

    return TenantResolu(tenant=TenantContexte(id=tenant.id, nom=tenant.nom, slug=tenant.slug))
