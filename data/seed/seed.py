"""Jeu de données de démonstration : tenant Événements Étoile (Yaoundé).

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

TENANT_SLUG = "etoile"
TENANT_NOM = "Événements Étoile"
TENANT_VILLE = "Yaoundé"
# Nom de fichier résolu dans data/logos/ par src/canaux/tenant.py (voir D24).
# Absent de ce dossier tant que personne n'y dépose etoile.png : l'en-tête du
# PDF se rabat alors sur le nom du tenant seul, sans erreur (voir D14).
TENANT_LOGO = "etoile.png"

EMAIL_GESTIONNAIRE = "gestionnaire@etoile-events.cm"
NOM_GESTIONNAIRE = "Gestionnaire Étoile"
MOT_DE_PASSE_DEMO = "Etoile-Demo-2026"

RESSOURCES = [
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

# La règle de quantité reprend le vocabulaire déjà fixé dans le besoin
# (type_evenement, nombre_invites, duree_jours...) décrit dans DONNEES.md
LIGNES_PAR_DEFAUT_MARIAGE = [
    LigneModeleAProvisionner(categorie="salle", base_calcul="duree_jours", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="mobilier", base_calcul="nombre_invites", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="restauration", base_calcul="nombre_invites", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="decoration", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="sonorisation", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="personnel", base_calcul="forfait", quantite_par_unite=1),
    LigneModeleAProvisionner(categorie="logistique", base_calcul="forfait", quantite_par_unite=1),
]

CONFIGURATION_ETOILE = ConfigurationTenant(
    nom=TENANT_NOM,
    slug=TENANT_SLUG,
    ville=TENANT_VILLE,
    logo=TENANT_LOGO,
    ressources=RESSOURCES,
    modele_mariage=LIGNES_PAR_DEFAUT_MARIAGE,
    gestionnaire=GestionnaireAProvisionner(
        email=EMAIL_GESTIONNAIRE, nom=NOM_GESTIONNAIRE, mot_de_passe=MOT_DE_PASSE_DEMO
    ),
)


def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        _, gestionnaire_cree = provisionner_tenant(session, CONFIGURATION_ETOILE)
        session.commit()

    print(
        f"Tenant « {TENANT_NOM} » (slug={TENANT_SLUG}) : "
        f"{len(RESSOURCES)} ressources, modèle Mariage à jour."
    )
    if gestionnaire_cree:
        print(f"Gestionnaire créé — email: {EMAIL_GESTIONNAIRE}  mot de passe: {MOT_DE_PASSE_DEMO}")
        print("Ces identifiants sont aussi consignés dans data/seed/README.md.")
    else:
        print(f"Gestionnaire déjà présent ({EMAIL_GESTIONNAIRE}), mot de passe inchangé.")


if __name__ == "__main__":
    main()
