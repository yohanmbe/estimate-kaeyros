from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Demande, Tenant
from src.indicateurs.demandes import compter_demandes, repartir_par_tranche_invites
from src.indicateurs.types import EffectifTranche, Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_demande(
    session: Session,
    tenant: Tenant,
    date_creation: datetime,
    besoin: dict | None = None,
    canal: str = "streamlit",
) -> Demande:
    demande = Demande(
        tenant_id=tenant.id,
        canal=canal,
        etat="complete",
        besoin=besoin or {},
        date_creation=date_creation,
    )
    session.add(demande)
    session.commit()
    return demande


def test_compte_seulement_les_demandes_du_tenant_dans_la_periode(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_demande(session, etoile, datetime(2026, 1, 10))
    creer_demande(session, etoile, datetime(2026, 1, 20))
    creer_demande(session, etoile, datetime(2025, 12, 31))  # avant la période
    creer_demande(session, etoile, datetime(2026, 2, 1))  # après la période
    creer_demande(session, fanta, datetime(2026, 1, 15))  # autre tenant

    assert compter_demandes(session, etoile.id, PERIODE_JANVIER) == 2


def test_aucune_demande_sur_la_periode_donne_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert compter_demandes(session, etoile.id, PERIODE_JANVIER) == 0


def test_demandes_bornant_exactement_la_periode_sont_incluses(session):
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile, PERIODE_JANVIER.debut)
    creer_demande(session, etoile, PERIODE_JANVIER.fin)

    assert compter_demandes(session, etoile.id, PERIODE_JANVIER) == 2


def test_repartition_par_tranche_invites_sur_quatre_demandes_et_une_sans_besoin(session):
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile, datetime(2026, 1, 5), besoin={"nombre_invites": 60})
    creer_demande(session, etoile, datetime(2026, 1, 6), besoin={"nombre_invites": 200})
    creer_demande(session, etoile, datetime(2026, 1, 7), besoin={"nombre_invites": 350})
    creer_demande(session, etoile, datetime(2026, 1, 8), besoin={"nombre_invites": 800})
    # Conversation interrompue avant que nombre_invites ne soit connu : dans
    # aucune tranche, mais toujours comptée par compter_demandes.
    creer_demande(session, etoile, datetime(2026, 1, 9), besoin={})
    # Hors période : ne doit compter dans aucune tranche.
    creer_demande(session, etoile, datetime(2026, 2, 1), besoin={"nombre_invites": 60})

    assert repartir_par_tranche_invites(session, etoile.id, PERIODE_JANVIER) == [
        EffectifTranche(tranche="< 100", nombre_demandes=1),
        EffectifTranche(tranche="100-250", nombre_demandes=1),
        EffectifTranche(tranche="251-500", nombre_demandes=1),
        EffectifTranche(tranche="500+", nombre_demandes=1),
    ]


def test_une_borne_de_tranche_ne_compte_que_dans_une_seule_tranche(session):
    """250 invités appartiennent à « 100-250 », 500 à « 251-500 » : sans ce
    test, un chevauchement de bornes ferait compter deux fois la même demande
    ou l'oublierait des deux côtés.
    """
    etoile = creer_tenant(session, "etoile")
    for jour, invites in enumerate((99, 100, 250, 251, 500, 501), start=5):
        creer_demande(session, etoile, datetime(2026, 1, jour), besoin={"nombre_invites": invites})

    assert repartir_par_tranche_invites(session, etoile.id, PERIODE_JANVIER) == [
        EffectifTranche(tranche="< 100", nombre_demandes=1),
        EffectifTranche(tranche="100-250", nombre_demandes=2),
        EffectifTranche(tranche="251-500", nombre_demandes=2),
        EffectifTranche(tranche="500+", nombre_demandes=1),
    ]


def test_repartition_ignore_les_demandes_dun_autre_tenant(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_demande(session, fanta, datetime(2026, 1, 5), besoin={"nombre_invites": 60})

    assert repartir_par_tranche_invites(session, etoile.id, PERIODE_JANVIER) == [
        EffectifTranche(tranche="< 100", nombre_demandes=0),
        EffectifTranche(tranche="100-250", nombre_demandes=0),
        EffectifTranche(tranche="251-500", nombre_demandes=0),
        EffectifTranche(tranche="500+", nombre_demandes=0),
    ]
