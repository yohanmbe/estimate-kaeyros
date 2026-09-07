from dataclasses import replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.hachage import verifie_mot_de_passe
from src.catalogue.provisionnement import (
    ConfigurationTenant,
    GestionnaireAProvisionner,
    LigneModeleAProvisionner,
    RessourceAProvisionner,
    configuration_depuis_dict,
    provisionner_tenant,
)
from src.db.models import ModeleEvenement, Ressource, Tenant, Utilisateur

CONFIGURATION_CLIENT_TEST = ConfigurationTenant(
    nom="Réceptions Douala",
    slug="receptions-douala",
    ville="Douala",
    logo="receptions-douala.png",
    ressources=[
        RessourceAProvisionner(
            nom="Salle Akwa",
            categorie="salle",
            unite_facturation="jour",
            prix_unitaire=400_000,
            attributs={"quartier": "Akwa", "capacite": 250},
        ),
        RessourceAProvisionner(
            nom="Menu Standard",
            categorie="restauration",
            unite_facturation="personne",
            prix_unitaire=7_500,
        ),
    ],
    modele_mariage=[
        LigneModeleAProvisionner(categorie="salle", base_calcul="duree_jours", quantite_par_unite=1),
        LigneModeleAProvisionner(
            categorie="restauration", base_calcul="nombre_invites", quantite_par_unite=1
        ),
    ],
    gestionnaire=GestionnaireAProvisionner(
        email="gestionnaire@receptions-douala.cm",
        nom="Gestionnaire Réceptions Douala",
        mot_de_passe="mot-de-passe-de-test",
    ),
)


def test_nouveau_tenant_cree_son_profil_son_catalogue_et_son_gestionnaire(session: Session):
    tenant, gestionnaire_cree = provisionner_tenant(session, CONFIGURATION_CLIENT_TEST)
    session.commit()

    assert gestionnaire_cree is True
    assert tenant.nom == "Réceptions Douala"
    assert tenant.logo == "receptions-douala.png"

    ressources = session.scalars(select(Ressource).where(Ressource.tenant_id == tenant.id)).all()
    assert {r.nom for r in ressources} == {"Salle Akwa", "Menu Standard"}

    modele = session.scalar(
        select(ModeleEvenement).where(ModeleEvenement.tenant_id == tenant.id)
    )
    assert modele.nom == "Mariage"
    assert len(modele.lignes_par_defaut) == 2

    gestionnaire = session.scalar(
        select(Utilisateur).where(Utilisateur.tenant_id == tenant.id)
    )
    assert verifie_mot_de_passe("mot-de-passe-de-test", gestionnaire.mot_de_passe_hache)


def test_relancer_le_provisionnement_ne_duplique_aucune_ressource(session: Session):
    provisionner_tenant(session, CONFIGURATION_CLIENT_TEST)
    session.commit()

    tenant, gestionnaire_cree = provisionner_tenant(session, CONFIGURATION_CLIENT_TEST)
    session.commit()

    ressources = session.scalars(select(Ressource).where(Ressource.tenant_id == tenant.id)).all()
    assert len(ressources) == 2
    assert gestionnaire_cree is False


def test_relancer_avec_un_nouveau_nom_met_a_jour_le_tenant_existant(session: Session):
    """Régression : get_or_create_tenant avait longtemps ignoré les tenants déjà
    créés, laissant nom/ville/logo figés au premier lancement (voir D25)."""
    provisionner_tenant(session, CONFIGURATION_CLIENT_TEST)
    session.commit()

    configuration_modifiee = ConfigurationTenant(
        nom="Réceptions Douala Prestige",
        slug=CONFIGURATION_CLIENT_TEST.slug,
        ville="Douala",
        logo="nouveau-logo.png",
        ressources=CONFIGURATION_CLIENT_TEST.ressources,
        modele_mariage=CONFIGURATION_CLIENT_TEST.modele_mariage,
        gestionnaire=CONFIGURATION_CLIENT_TEST.gestionnaire,
    )
    tenant, _ = provisionner_tenant(session, configuration_modifiee)
    session.commit()

    assert tenant.nom == "Réceptions Douala Prestige"
    assert tenant.logo == "nouveau-logo.png"
    assert session.scalar(select(Tenant).where(Tenant.slug == "receptions-douala")) is tenant


def test_relancer_ne_modifie_pas_le_mot_de_passe_dun_gestionnaire_existant(session: Session):
    provisionner_tenant(session, CONFIGURATION_CLIENT_TEST)
    session.commit()

    configuration_autre_mot_de_passe = replace(
        CONFIGURATION_CLIENT_TEST,
        gestionnaire=replace(
            CONFIGURATION_CLIENT_TEST.gestionnaire, mot_de_passe="un-autre-mot-de-passe"
        ),
    )
    tenant, gestionnaire_cree = provisionner_tenant(session, configuration_autre_mot_de_passe)
    session.commit()

    gestionnaire = session.scalar(
        select(Utilisateur).where(Utilisateur.tenant_id == tenant.id)
    )
    assert gestionnaire_cree is False
    assert verifie_mot_de_passe("mot-de-passe-de-test", gestionnaire.mot_de_passe_hache)
    assert not verifie_mot_de_passe("un-autre-mot-de-passe", gestionnaire.mot_de_passe_hache)


def test_configuration_valide_est_convertie_sans_erreur():
    configuration = configuration_depuis_dict(
        {
            "nom": "Réceptions Douala",
            "slug": "receptions-douala",
            "ville": "Douala",
            "logo": "receptions-douala.png",
            "ressources": [
                {
                    "nom": "Salle Akwa",
                    "categorie": "salle",
                    "unite_facturation": "jour",
                    "prix_unitaire": 400_000,
                    "attributs": {"quartier": "Akwa"},
                }
            ],
            "modele_mariage": [
                {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1}
            ],
            "gestionnaire": {
                "email": "gestionnaire@receptions-douala.cm",
                "nom": "Gestionnaire",
                "mot_de_passe": "temporaire",
            },
        }
    )

    assert configuration.slug == "receptions-douala"
    assert configuration.ressources[0].attributs == {"quartier": "Akwa"}


def test_configuration_sans_logo_ni_ville_est_acceptee():
    configuration = configuration_depuis_dict(
        {
            "nom": "Réceptions Douala",
            "slug": "receptions-douala",
            "ressources": [],
            "modele_mariage": [],
            "gestionnaire": {
                "email": "gestionnaire@receptions-douala.cm",
                "nom": "Gestionnaire",
                "mot_de_passe": "temporaire",
            },
        }
    )

    assert configuration.ville is None
    assert configuration.logo is None


def test_configuration_sans_slug_est_signalee_par_une_erreur_claire():
    with pytest.raises(ValueError, match="slug"):
        configuration_depuis_dict(
            {
                "nom": "Réceptions Douala",
                "ressources": [],
                "modele_mariage": [],
                "gestionnaire": {
                    "email": "gestionnaire@receptions-douala.cm",
                    "nom": "Gestionnaire",
                    "mot_de_passe": "temporaire",
                },
            }
        )


def test_gestionnaire_sans_mot_de_passe_est_signale_par_une_erreur_claire():
    with pytest.raises(ValueError, match="mot_de_passe"):
        configuration_depuis_dict(
            {
                "nom": "Réceptions Douala",
                "slug": "receptions-douala",
                "ressources": [],
                "modele_mariage": [],
                "gestionnaire": {
                    "email": "gestionnaire@receptions-douala.cm",
                    "nom": "Gestionnaire",
                },
            }
        )
