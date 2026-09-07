"""Jeu de données de démonstration : quatre tenants événementiels à Yaoundé,
de gammes de prix différentes, pour des tests multi-locataires réalistes.

Idempotent : relancer ce script ne duplique rien (voir
src/catalogue/provisionnement.py, partagé avec data/seed/ajouter_tenant.py
pour un vrai client).
"""
import os
import sys
from pathlib import Path

# Permet de lancer ce fichier directement (uv run python data/seed/seed.py)
# sans que la racine du projet soit déjà sur le sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.catalogue.provisionnement import (
    ConfigurationTenant,
    GestionnaireAProvisionner,
    LigneModeleAProvisionner,
    RessourceAProvisionner,
    provisionner_tenant,
)

# Le champ logo de chaque configuration est un nom de fichier résolu dans
# data/logos/ par src/canaux/tenant.py (voir D24). Absent de ce dossier tant
# que personne n'y dépose l'image : l'en-tête du PDF se rabat alors sur le
# nom du tenant seul, sans erreur (voir D14).

# La règle de quantité reprend le vocabulaire déjà fixé dans le besoin
# (type_evenement, nombre_invites, duree_jours...) décrit dans DONNEES.md.
# Identique pour les quatre tenants : le modèle Mariage ne varie pas, seuls
# les catalogues et les prix distinguent les tenants (voir périmètre v1 dans
# CLAUDE.md : un seul type d'événement).
LIGNES_PAR_DEFAUT_MARIAGE = [
    LigneModeleAProvisionner(categorie="salle", base_calcul="duree_jours", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="mobilier", base_calcul="nombre_invites", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="restauration", base_calcul="nombre_invites", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="decoration", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="sonorisation", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="personnel", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="logistique", base_calcul="forfait", quantite_par_unite=1),
]

# --- Tenant 1 : Événements Étoile — gamme intermédiaire/haute ---------------

RESSOURCES_ETOILE = [
    RessourceAProvisionner(
        nom="Salle Étoile Bastos",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=450_000,
        attributs={"quartier": "Bastos", "capacite": 300},
    ),
    RessourceAProvisionner(
        nom="Salle Étoile Odza",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=250_000,
        attributs={"quartier": "Odza", "capacite": 150},
    ),
    RessourceAProvisionner(
        nom="Salle Étoile Mvan",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=600_000,
        attributs={"quartier": "Mvan", "capacite": 500},
    ),
    RessourceAProvisionner(
        nom="Chaise Napoléon dorée",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=1_500,
        attributs={"style": "Napoléon doré"},
    ),
    RessourceAProvisionner(
        nom="Chaise pliante housse blanche",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=1_000,
        attributs={"style": "pliante avec housse"},
    ),
    RessourceAProvisionner(
        nom="Menu Prestige buffet complet",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=15_000,
    ),
    RessourceAProvisionner(
        nom="Menu Standard",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=8_000,
    ),
    RessourceAProvisionner(
        nom="Cocktail dînatoire",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=5_000,
    ),
    RessourceAProvisionner(
        nom="Décoration florale premium",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=500_000,
    ),
    RessourceAProvisionner(
        nom="Décoration thématique standard",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=250_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation complète avec DJ",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=400_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation standard",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=200_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie bilingue",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=150_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie standard",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=80_000,
    ),
    RessourceAProvisionner(
        nom="Installation et logistique complète",
        categorie="logistique",
        unite_facturation="forfait",
        prix_unitaire=300_000,
    ),
]

CONFIGURATION_ETOILE = ConfigurationTenant(
    nom="Événements Étoile",
    slug="etoile",
    ville="Yaoundé",
    logo="etoile.png",
    coordonnees="671234567, Bastos",
    ressources=RESSOURCES_ETOILE,
    modele_mariage=LIGNES_PAR_DEFAUT_MARIAGE,
    gestionnaire=GestionnaireAProvisionner(
        email="gestionnaire@etoile.com",
        nom="Gestionnaire Étoile",
        mot_de_passe="passe",
    ),
)
# Coordonnées ajoutées par provisionner_tenant via ConfigurationTenant

# --- Tenant 2 : Yaoundé Prestige — haut de gamme ---------------------------

RESSOURCES_PRESTIGE = [
    RessourceAProvisionner(
        nom="Salle Prestige Bastos",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=750_000,
        attributs={"quartier": "Bastos", "capacite": 400},
    ),
    RessourceAProvisionner(
        nom="Salle Prestige Golf",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=900_000,
        attributs={"quartier": "Golf", "capacite": 600},
    ),
    RessourceAProvisionner(
        nom="Salle Prestige Warda",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=1_100_000,
        attributs={"quartier": "Warda", "capacite": 800},
    ),
    RessourceAProvisionner(
        nom="Chaise Chiavari dorée",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=2_500,
        attributs={"style": "Chiavari doré"},
    ),
    RessourceAProvisionner(
        nom="Chaise Tiffany blanche",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=2_000,
        attributs={"style": "Tiffany blanc"},
    ),
    RessourceAProvisionner(
        nom="Menu Signature cinq services",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=25_000,
    ),
    RessourceAProvisionner(
        nom="Menu Gastronomique",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=18_000,
    ),
    RessourceAProvisionner(
        nom="Cocktail chic",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=9_000,
    ),
    RessourceAProvisionner(
        nom="Décoration florale haut de gamme",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=900_000,
    ),
    RessourceAProvisionner(
        nom="Décoration scénique sur mesure",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=600_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation premium avec éclairage",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=700_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation standard Prestige",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=350_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie renommé",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=300_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie bilingue Prestige",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=180_000,
    ),
    RessourceAProvisionner(
        nom="Installation et logistique complète Prestige",
        categorie="logistique",
        unite_facturation="forfait",
        prix_unitaire=450_000,
    ),
]

CONFIGURATION_PRESTIGE = ConfigurationTenant(
    nom="Yaoundé Prestige",
    slug="prestige",
    ville="Yaoundé",
    logo="prestige.png",
    coordonnees="677654321, Golf",
    ressources=RESSOURCES_PRESTIGE,
    modele_mariage=LIGNES_PAR_DEFAUT_MARIAGE,
    gestionnaire=GestionnaireAProvisionner(
        email="gestionnaire@prestige.com",
        nom="Gestionnaire Prestige",
        mot_de_passe="passe",
    ),
)

# --- Tenant 3 : Mariage Malin — économique ---------------------------------

RESSOURCES_MALIN = [
    RessourceAProvisionner(
        nom="Salle Éco Nkoabang",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=120_000,
        attributs={"quartier": "Nkoabang", "capacite": 100},
    ),
    RessourceAProvisionner(
        nom="Salle Éco Ekounou",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=180_000,
        attributs={"quartier": "Ekounou", "capacite": 200},
    ),
    RessourceAProvisionner(
        nom="Salle Éco Etoudi",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=280_000,
        attributs={"quartier": "Etoudi", "capacite": 350},
    ),
    RessourceAProvisionner(
        nom="Chaise plastique simple",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=500,
        attributs={"style": "plastique simple"},
    ),
    RessourceAProvisionner(
        nom="Chaise pliante housse basique",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=800,
        attributs={"style": "pliante avec housse basique"},
    ),
    RessourceAProvisionner(
        nom="Menu Économique",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=3_500,
    ),
    RessourceAProvisionner(
        nom="Menu Standard Malin",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=5_500,
    ),
    RessourceAProvisionner(
        nom="Cocktail simple",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=3_000,
    ),
    RessourceAProvisionner(
        nom="Décoration basique",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=100_000,
    ),
    RessourceAProvisionner(
        nom="Décoration thématique légère",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=150_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation compacte",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=100_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation standard Malin",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=150_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie débutant",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=40_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie expérimenté Malin",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=70_000,
    ),
    RessourceAProvisionner(
        nom="Installation logistique de base",
        categorie="logistique",
        unite_facturation="forfait",
        prix_unitaire=90_000,
    ),
]

CONFIGURATION_MALIN = ConfigurationTenant(
    nom="Mariage Malin",
    slug="malin",
    ville="Yaoundé",
    logo="malin.png",
    coordonnees="650123456, Nkoabang",
    ressources=RESSOURCES_MALIN,
    modele_mariage=LIGNES_PAR_DEFAUT_MARIAGE,
    gestionnaire=GestionnaireAProvisionner(
        email="gestionnaire@malin.com",
        nom="Gestionnaire Malin",
        mot_de_passe="passe",
    ),
)

# --- Tenant 4 : Nlongkak Réceptions — milieu de gamme ----------------------

RESSOURCES_NLONGKAK = [
    RessourceAProvisionner(
        nom="Salle Nlongkak Jardin",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=350_000,
        attributs={"quartier": "Nlongkak", "capacite": 250},
    ),
    RessourceAProvisionner(
        nom="Salle Essos Panorama",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=280_000,
        attributs={"quartier": "Essos", "capacite": 180},
    ),
    RessourceAProvisionner(
        nom="Salle Mendong Events",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=500_000,
        attributs={"quartier": "Mendong", "capacite": 400},
    ),
    RessourceAProvisionner(
        nom="Chaise Napoléon blanche",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=1_200,
        attributs={"style": "Napoléon blanc"},
    ),
    RessourceAProvisionner(
        nom="Chaise pliante housse dorée",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=900,
        attributs={"style": "pliante avec housse dorée"},
    ),
    RessourceAProvisionner(
        nom="Menu Traditionnel Camerounais",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=10_000,
    ),
    RessourceAProvisionner(
        nom="Menu Fusion",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=12_000,
    ),
    RessourceAProvisionner(
        nom="Cocktail convivial",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=6_000,
    ),
    RessourceAProvisionner(
        nom="Décoration florale classique",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=350_000,
    ),
    RessourceAProvisionner(
        nom="Décoration minimaliste",
        categorie="decoration",
        unite_facturation="forfait",
        prix_unitaire=200_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation avec animation DJ",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=320_000,
    ),
    RessourceAProvisionner(
        nom="Sonorisation de base Nlongkak",
        categorie="sonorisation",
        unite_facturation="forfait",
        prix_unitaire=160_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie bilingue Nlongkak",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=120_000,
    ),
    RessourceAProvisionner(
        nom="Maître de cérémonie local",
        categorie="personnel",
        unite_facturation="forfait",
        prix_unitaire=60_000,
    ),
    RessourceAProvisionner(
        nom="Installation et logistique standard Nlongkak",
        categorie="logistique",
        unite_facturation="forfait",
        prix_unitaire=220_000,
    ),
]

CONFIGURATION_NLONGKAK = ConfigurationTenant(
    nom="Nlongkak Réceptions",
    slug="nlongkak",
    ville="Yaoundé",
    logo="receptions.png",
    coordonnees="693456789, Nlongkak",
    ressources=RESSOURCES_NLONGKAK,
    modele_mariage=LIGNES_PAR_DEFAUT_MARIAGE,
    gestionnaire=GestionnaireAProvisionner(
        email="gestionnaire@nlongkak.com",
        nom="Gestionnaire Nlongkak",
        mot_de_passe="passe",
    ),
)

CONFIGURATIONS = [
    CONFIGURATION_ETOILE,
    CONFIGURATION_PRESTIGE,
    CONFIGURATION_MALIN,
    CONFIGURATION_NLONGKAK,
]


def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        for configuration in CONFIGURATIONS:
            tenant, gestionnaire_cree = provisionner_tenant(session, configuration)
            session.commit()

            print(
                f"Tenant « {configuration.nom} » (slug={configuration.slug}) : "
                f"{len(configuration.ressources)} ressources, modèle Mariage à jour."
            )
            print(f"  Coordonnées : {tenant.coordonnees}")
            if gestionnaire_cree:
                print(
                    f"  Gestionnaire créé — email: {configuration.gestionnaire.email}  "
                    f"mot de passe: {configuration.gestionnaire.mot_de_passe}"
                )
            else:
                print(
                    f"  Gestionnaire déjà présent ({configuration.gestionnaire.email}), "
                    "mot de passe inchangé."
                )

    print("Identifiants de démonstration consignés dans data/seed/README.md.")


if __name__ == "__main__":
    main()
