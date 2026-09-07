"""Résolution du tenant du prospect à partir du slug de l'URL (voir CLAUDE.md, Multi-locataires)"""
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.canaux.types import ResolutionTenant, TenantContexte, TenantIndisponible, TenantResolu
from src.db.models import Tenant

# Tenant.logo ne stocke qu'un nom de fichier, jamais un chemin absolu ni relatif
# au répertoire de travail : un chemin absolu ne survivrait pas à un déploiement
# sur une autre machine, un chemin relatif dépendrait de l'endroit d'où
# Streamlit est lancé. La résolution se fait une seule fois ici, pour que tous
# les canaux et le futur tableau de bord partagent la même convention (D24).
DOSSIER_LOGOS = Path(__file__).resolve().parents[2] / "data" / "logos"


def extraire_slug_depuis_url() -> str | None:
    """Lit le slug dans les paramètres de l'URL Streamlit (?slug=...), absent si non fourni"""
    import streamlit as st

    return st.query_params.get("slug")


def resoudre_chemin_logo(nom_fichier: str | None, dossier: Path = DOSSIER_LOGOS) -> str | None:
    """Résout le nom de fichier logo d'un tenant en chemin utilisable, ou None.

    Renvoie None si aucun nom n'est enregistré ou si le fichier n'existe pas
    sur le disque : l'appelant (l'en-tête du PDF, voir D14) se rabat alors
    proprement sur un en-tête sans logo, plutôt que de planter.
    """
    if not nom_fichier:
        return None
    chemin = dossier / nom_fichier
    return str(chemin) if chemin.is_file() else None


def charger_tenant(session: Session, tenant_id: str) -> TenantContexte | None:
    """Charge le tenant par son identifiant, pour le tableau de bord du gestionnaire.

    Le prospect arrive par un slug d'URL (D16), le gestionnaire par sa
    connexion : son tenant_id est déjà établi en session, il n'y a rien à
    résoudre, seulement le nom, les coordonnées et le logo à afficher.
    """
    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        return None
    return TenantContexte(
        id=tenant.id,
        nom=tenant.nom,
        slug=tenant.slug,
        logo=resoudre_chemin_logo(tenant.logo),
        coordonnees=tenant.coordonnees,
    )


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

    return TenantResolu(
        tenant=TenantContexte(
            id=tenant.id,
            nom=tenant.nom,
            slug=tenant.slug,
            logo=resoudre_chemin_logo(tenant.logo),
            coordonnees=tenant.coordonnees,
        )
    )
