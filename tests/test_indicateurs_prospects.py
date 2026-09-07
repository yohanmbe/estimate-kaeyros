from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Prospect, Tenant
from src.indicateurs.prospects import calculer_taux_consentement_contact
from src.indicateurs.types import Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_prospect(
    session: Session, tenant: Tenant, date_creation: datetime, consentement_contact: bool
) -> Prospect:
    prospect = Prospect(
        tenant_id=tenant.id,
        nom="Prospect Test",
        telephone="699000000",
        consentement_contact=consentement_contact,
        date_creation=date_creation,
    )
    session.add(prospect)
    session.commit()
    return prospect


def test_taux_consentement_sur_quatre_prospects_dont_trois_consentants(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, datetime(2026, 1, 5), consentement_contact=True)
    creer_prospect(session, etoile, datetime(2026, 1, 10), consentement_contact=True)
    creer_prospect(session, etoile, datetime(2026, 1, 15), consentement_contact=True)
    creer_prospect(session, etoile, datetime(2026, 1, 20), consentement_contact=False)
    # Hors période : ne doit pas peser dans le calcul.
    creer_prospect(session, etoile, datetime(2026, 2, 1), consentement_contact=False)

    assert calculer_taux_consentement_contact(session, etoile.id, PERIODE_JANVIER) == 75


def test_taux_consentement_arrondit_au_pourcent_le_plus_proche_sans_flottant(session):
    etoile = creer_tenant(session, "etoile")
    # 2 consentants sur 3 : 66,666...% -> arrondi à 67.
    creer_prospect(session, etoile, datetime(2026, 1, 5), consentement_contact=True)
    creer_prospect(session, etoile, datetime(2026, 1, 10), consentement_contact=True)
    creer_prospect(session, etoile, datetime(2026, 1, 15), consentement_contact=False)

    assert calculer_taux_consentement_contact(session, etoile.id, PERIODE_JANVIER) == 67


def test_taux_consentement_ignore_les_prospects_dun_autre_tenant(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_prospect(session, fanta, datetime(2026, 1, 5), consentement_contact=True)

    assert calculer_taux_consentement_contact(session, etoile.id, PERIODE_JANVIER) == 0


def test_taux_consentement_sans_prospect_sur_la_periode_est_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert calculer_taux_consentement_contact(session, etoile.id, PERIODE_JANVIER) == 0
