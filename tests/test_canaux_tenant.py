from sqlalchemy.orm import Session

from src.canaux.tenant import resoudre_chemin_logo, resoudre_tenant
from src.canaux.types import TenantIndisponible, TenantResolu
from src.db.models import Tenant


def creer_tenant(
    session: Session,
    slug: str,
    actif: bool = True,
    logo: str | None = None,
    coordonnees: str | None = None,
) -> Tenant:
    tenant = Tenant(
        nom=f"Entreprise {slug}", slug=slug, actif=actif, logo=logo, coordonnees=coordonnees
    )
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


def test_tenant_sans_logo_enregistre_est_resolu_sans_logo(session):
    creer_tenant(session, slug="etoile", logo=None)

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.logo is None


def test_tenant_avec_un_nom_de_logo_sans_fichier_correspondant_est_resolu_sans_logo(session):
    """data/logos/ ne contient jamais de fichier pour cette entreprise fictive :
    un nom enregistré sans fichier ne doit pas faire planter la résolution."""
    creer_tenant(session, slug="etoile", logo="fichier-jamais-depose.png")

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.logo is None


def test_coordonnees_du_tenant_sont_transmises_au_contexte(session):
    creer_tenant(session, slug="etoile", coordonnees="671234567, Bastos")

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.coordonnees == "671234567, Bastos"


def test_tenant_sans_coordonnees_enregistrees_est_resolu_sans_coordonnees(session):
    creer_tenant(session, slug="etoile", coordonnees=None)

    resultat = resoudre_tenant(session, slug="etoile")

    assert isinstance(resultat, TenantResolu)
    assert resultat.tenant.coordonnees is None


def test_nom_de_logo_absent_ne_cherche_aucun_fichier():
    assert resoudre_chemin_logo(None) is None


def test_nom_de_logo_avec_fichier_present_renvoie_son_chemin_complet(tmp_path):
    (tmp_path / "etoile.png").write_bytes(b"contenu-image-de-test")

    chemin = resoudre_chemin_logo("etoile.png", dossier=tmp_path)

    assert chemin == str(tmp_path / "etoile.png")


def test_nom_de_logo_sans_fichier_present_renvoie_aucun_chemin(tmp_path):
    chemin = resoudre_chemin_logo("absent.png", dossier=tmp_path)

    assert chemin is None
