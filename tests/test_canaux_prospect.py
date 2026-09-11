from sqlalchemy.orm import Session

from src.canaux.prospect import enregistrer_prospect
from src.db.models import Prospect, Tenant


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def test_telephone_jamais_vu_cree_une_ligne_prospect(session):
    etoile = creer_tenant(session, "etoile")

    contexte = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", "sylvie@example.cm", True
    )

    prospects = session.query(Prospect).all()
    assert len(prospects) == 1
    assert contexte.id == prospects[0].id


def test_meme_tenant_et_meme_telephone_renvoie_la_fiche_existante(session):
    etoile = creer_tenant(session, "etoile")
    premier = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", "sylvie@example.cm", True
    )

    second = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", "sylvie@example.cm", True
    )

    assert second.id == premier.id
    assert session.query(Prospect).count() == 1


def test_fiche_existante_nest_jamais_modifiee_par_une_visite_suivante(session):
    etoile = creer_tenant(session, "etoile")
    enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", "sylvie@example.cm", True
    )

    revisite = enregistrer_prospect(
        session, etoile.id, "Sylvie N.", "699001122", "autre@example.cm", False
    )

    assert revisite.nom == "Sylvie Nkoa"
    assert revisite.email == "sylvie@example.cm"
    assert revisite.consentement_contact is True


def test_meme_telephone_dans_un_autre_tenant_cree_une_ligne_distincte(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    premier = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", None, True
    )

    second = enregistrer_prospect(session, fanta.id, "Sylvie Nkoa", "699001122", None, True)

    assert second.id != premier.id
    assert session.query(Prospect).count() == 2
