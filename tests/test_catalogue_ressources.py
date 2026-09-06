from sqlalchemy.orm import Session

from src.catalogue.ressources import charger_modele_evenement, charger_ressources_actives
from src.db.models import ModeleEvenement, Ressource, Tenant


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_ressource(
    session: Session, tenant: Tenant, nom: str, categorie: str = "salle", actif: bool = True
) -> Ressource:
    ressource = Ressource(
        tenant_id=tenant.id,
        nom=nom,
        categorie=categorie,
        unite_facturation="jour",
        prix_unitaire=450_000,
        attributs={"capacite": 300, "quartier": "Bastos"},
        actif=actif,
    )
    session.add(ressource)
    session.commit()
    return ressource


def test_catalogue_ne_contient_que_les_ressources_du_tenant_demande(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_ressource(session, etoile, "Salle Étoile")
    creer_ressource(session, fanta, "Salle Fanta")

    catalogue = charger_ressources_actives(session, etoile.id)

    assert [ressource.nom for ressource in catalogue] == ["Salle Étoile"]


def test_ressource_desactivee_nest_pas_proposee_au_prospect(session):
    etoile = creer_tenant(session, "etoile")
    creer_ressource(session, etoile, "Salle retirée du catalogue", actif=False)
    creer_ressource(session, etoile, "Salle Étoile")

    catalogue = charger_ressources_actives(session, etoile.id)

    assert [ressource.nom for ressource in catalogue] == ["Salle Étoile"]


def test_modele_evenement_traduit_les_bases_de_calcul_vers_le_vocabulaire_du_moteur(session):
    etoile = creer_tenant(session, "etoile")
    session.add(
        ModeleEvenement(
            tenant_id=etoile.id,
            nom="Mariage",
            lignes_par_defaut=[
                {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1},
                {"categorie": "mobilier", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
                {"categorie": "decoration", "base_calcul": "forfait", "quantite_par_unite": 1},
            ],
        )
    )
    session.commit()

    modele = charger_modele_evenement(session, etoile.id, "Mariage")

    assert [(regle.categorie, regle.base) for regle in modele] == [
        ("salle", "jour"),
        ("mobilier", "invite"),
        ("decoration", "forfait"),
    ]


def test_tenant_sans_modele_devenement_est_signale_plutot_que_chiffre_a_zero(session):
    etoile = creer_tenant(session, "etoile")

    assert charger_modele_evenement(session, etoile.id, "Mariage") is None


def test_modele_devenement_dun_autre_tenant_nest_jamais_utilise(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    session.add(
        ModeleEvenement(
            tenant_id=fanta.id,
            nom="Mariage",
            lignes_par_defaut=[
                {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1}
            ],
        )
    )
    session.commit()

    assert charger_modele_evenement(session, etoile.id, "Mariage") is None
