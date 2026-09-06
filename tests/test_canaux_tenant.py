from sqlalchemy.orm import Session

from src.canaux.tenant import resoudre_tenant
from src.canaux.types import TenantIndisponible, TenantResolu
from src.db.models import Tenant


def creer_tenant(session: Session, slug: str, actif: bool = True) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug, actif=actif)
    session.add(tenant)
    session.commit()
    return tenant


def test_slug_absent_ne_demarre_pas_la_conversation(session):
    resultat = resoudre_tenant(session, slug=None)

    assert resultat == TenantIndisponible(raison="slug_absent")


def test_slug_vide_est_traite_comme_absent(session):
    resultat = resoudre_tenant(session, slug="")

    assert resultat == TenantIndisponible(raison="slug_absent")


def test_slug_inconnu_ne_renvoie_aucun_tenant_par_defaut(session):
    creer_tenant(session, slug="etoile")

    resultat = resoudre_tenant(session, slug="inconnu")

    assert resultat == TenantIndisponible(raison="slug_inconnu")


def test_tenant_desactive_est_signale_et_non_resolu(session):
    creer_tenant(session, slug="etoile", actif=False)

    resultat = resoudre_tenant(session, slug="etoile")

    assert resultat == TenantIndisponible(raison="tenant_inactif")


def test_slug_connu_et_tenant_actif_est_resolu(session):
    tenant = creer_tenant(session, slug="etoile")

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.id == tenant.id
    assert resultat.tenant.slug == "etoile"


def test_deux_tenants_avec_slug_partage_un_prefixe_ne_sont_pas_confondus(session):
    creer_tenant(session, slug="etoile")
    creer_tenant(session, slug="etoile2")

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.slug == "etoile"
