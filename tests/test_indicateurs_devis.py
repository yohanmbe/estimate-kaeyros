from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Demande, Devis, Tenant
from src.indicateurs.devis import calculer_montant_moyen, calculer_montant_total
from src.indicateurs.types import Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_demande(session: Session, tenant: Tenant) -> Demande:
    demande = Demande(tenant_id=tenant.id, canal="streamlit", etat="complete", besoin={})
    session.add(demande)
    session.commit()
    return demande


def creer_devis(session: Session, tenant: Tenant, demande: Demande, total: int, date_emission: datetime) -> Devis:
    devis = Devis(
        tenant_id=tenant.id,
        demande_id=demande.id,
        lignes=[],
        total=total,
        date_emission=date_emission,
        date_validite=date_emission,
    )
    session.add(devis)
    session.commit()
    return devis


def test_montant_total_sur_trois_devis_de_la_periode_calcule_au_franc_pres(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile)
    creer_devis(session, etoile, demande, 400_000, datetime(2026, 1, 5))
    creer_devis(session, etoile, demande, 300_000, datetime(2026, 1, 15))
    creer_devis(session, etoile, demande, 200_000, datetime(2026, 1, 25))
    creer_devis(session, etoile, demande, 999_999, datetime(2025, 12, 31))  # avant la période
    creer_devis(session, etoile, demande, 999_999, datetime(2026, 2, 1))  # après la période

    assert calculer_montant_total(session, etoile.id, PERIODE_JANVIER) == 900_000


def test_montant_total_ignore_les_devis_dun_autre_tenant(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    demande_fanta = creer_demande(session, fanta)
    creer_devis(session, fanta, demande_fanta, 1_000_000, datetime(2026, 1, 10))

    assert calculer_montant_total(session, etoile.id, PERIODE_JANVIER) == 0


def test_montant_total_sans_devis_sur_la_periode_est_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert calculer_montant_total(session, etoile.id, PERIODE_JANVIER) == 0


def test_montant_moyen_sur_trois_devis_divisibles_exactement(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile)
    creer_devis(session, etoile, demande, 400_000, datetime(2026, 1, 5))
    creer_devis(session, etoile, demande, 300_000, datetime(2026, 1, 15))
    creer_devis(session, etoile, demande, 200_000, datetime(2026, 1, 25))

    assert calculer_montant_moyen(session, etoile.id, PERIODE_JANVIER) == 300_000


def test_montant_moyen_arrondit_au_franc_le_plus_proche_sans_flottant(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile)
    # Total 300 001 sur 2 devis : moyenne exacte 150 000,5 -> arrondie à 150 001.
    creer_devis(session, etoile, demande, 150_000, datetime(2026, 1, 5))
    creer_devis(session, etoile, demande, 150_001, datetime(2026, 1, 15))

    assert calculer_montant_moyen(session, etoile.id, PERIODE_JANVIER) == 150_001


def test_montant_moyen_sans_devis_sur_la_periode_est_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert calculer_montant_moyen(session, etoile.id, PERIODE_JANVIER) == 0
