"""Contraintes du modèle Prospect : nom et téléphone obligatoires, le reste non"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import Prospect, Tenant


def _creer_tenant(session: Session) -> Tenant:
    tenant = Tenant(nom="Réceptions Douala", slug="receptions-douala")
    session.add(tenant)
    session.flush()
    return tenant


def test_prospect_avec_nom_et_telephone_est_cree(session: Session):
    tenant = _creer_tenant(session)

    prospect = Prospect(tenant_id=tenant.id, nom="Awa Ngo", telephone="+237690000000")
    session.add(prospect)
    session.flush()

    assert prospect.email is None
    assert prospect.consentement_contact is True


def test_prospect_sans_telephone_est_refuse(session: Session):
    tenant = _creer_tenant(session)

    session.add(Prospect(tenant_id=tenant.id, nom="Awa Ngo"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_prospect_sans_nom_est_refuse(session: Session):
    tenant = _creer_tenant(session)

    session.add(Prospect(tenant_id=tenant.id, telephone="+237690000000"))
    with pytest.raises(IntegrityError):
        session.flush()
