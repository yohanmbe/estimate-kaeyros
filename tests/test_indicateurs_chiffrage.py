from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Demande, Devis, Tenant
from src.indicateurs.chiffrage import calculer_taux_demandes_chiffrees
from src.indicateurs.types import Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_demande(session: Session, tenant: Tenant, date_creation: datetime) -> Demande:
    demande = Demande(tenant_id=tenant.id, canal="streamlit", etat="complete", besoin={}, date_creation=date_creation)
    session.add(demande)
    session.commit()
    return demande


def creer_devis(session: Session, tenant: Tenant, demande: Demande) -> Devis:
    devis = Devis(
        tenant_id=tenant.id,
        demande_id=demande.id,
        lignes=[],
        total=100_000,
        date_emission=demande.date_creation,
    )
    session.add(devis)
    session.commit()
    return devis


def test_taux_de_demandes_chiffrees_sur_quatre_demandes_dont_trois_avec_devis(session):
    etoile = creer_tenant(session, "etoile")
    d1 = creer_demande(session, etoile, datetime(2026, 1, 5))
    d2 = creer_demande(session, etoile, datetime(2026, 1, 10))
    d3 = creer_demande(session, etoile, datetime(2026, 1, 15))
    creer_demande(session, etoile, datetime(2026, 1, 20))  # jamais chiffrée
    creer_devis(session, etoile, d1)
    creer_devis(session, etoile, d2)
    # d3 a deux devis émis (options reprises) : ne doit compter qu'une fois.
    creer_devis(session, etoile, d3)
    creer_devis(session, etoile, d3)

    assert calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE_JANVIER) == 75


def test_taux_de_demandes_chiffrees_arrondit_au_pourcent_le_plus_proche_sans_flottant(session):
    etoile = creer_tenant(session, "etoile")
    d1 = creer_demande(session, etoile, datetime(2026, 1, 5))
    creer_demande(session, etoile, datetime(2026, 1, 10))
    creer_demande(session, etoile, datetime(2026, 1, 15))
    creer_devis(session, etoile, d1)
    # 1 chiffrée sur 3 : 33,333...% -> arrondi à 33.

    assert calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE_JANVIER) == 33


def test_taux_de_demandes_chiffrees_ignore_devis_dune_demande_hors_periode(session):
    etoile = creer_tenant(session, "etoile")
    d1 = creer_demande(session, etoile, datetime(2025, 12, 20))  # hors période
    creer_devis(session, etoile, d1)
    creer_demande(session, etoile, datetime(2026, 1, 5))  # dans la période, jamais chiffrée

    assert calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE_JANVIER) == 0


def test_taux_de_demandes_chiffrees_ignore_les_demandes_dun_autre_tenant(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    d1 = creer_demande(session, fanta, datetime(2026, 1, 5))
    creer_devis(session, fanta, d1)

    assert calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE_JANVIER) == 0


def test_taux_de_demandes_chiffrees_sans_demande_sur_la_periode_est_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE_JANVIER) == 0
