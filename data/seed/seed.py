"""Jeu de données de démonstration : tenant Événements Étoile (Yaoundé).

Idempotent : chaque entité est recherchée par sa clé métier avant d'être
créée ou mise à jour, jamais insérée à l'aveugle. Relancer ce script ne
duplique rien. Voir data/seed/README.md pour les identifiants générés.
"""
import os
import sys
from pathlib import Path

# Permet de lancer ce fichier directement (uv run python data/seed/seed.py)
# sans que la racine du projet soit déjà sur le sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.auth.hachage import hash_mot_de_passe
from src.db.models import ModeleEvenement, Ressource, Tenant, Utilisateur

TENANT_SLUG = "etoile"
TENANT_NOM = "Événements Étoile"
TENANT_VILLE = "Yaoundé"

EMAIL_GESTIONNAIRE = "gestionnaire@etoile-events.cm"
NOM_GESTIONNAIRE = "Gestionnaire Étoile"
MOT_DE_PASSE_DEMO = "Etoile-Demo-2026"

RESSOURCES = [
    {
        "nom": "Salle Étoile Bastos",
        "categorie": "salle",
        "unite_facturation": "jour",
        "prix_unitaire": 450_000,
        "attributs": {"quartier": "Bastos", "capacite": 300},
    },
    {
        "nom": "Salle Étoile Odza",
        "categorie": "salle",
        "unite_facturation": "jour",
        "prix_unitaire": 250_000,
        "attributs": {"quartier": "Odza", "capacite": 150},
    },
    {
        "nom": "Salle Étoile Mvan",
        "categorie": "salle",
        "unite_facturation": "jour",
        "prix_unitaire": 600_000,
        "attributs": {"quartier": "Mvan", "capacite": 500},
    },
    {
        "nom": "Chaise Napoléon dorée",
        "categorie": "mobilier",
        "unite_facturation": "unite",
        "prix_unitaire": 1_500,
        "attributs": {"style": "Napoléon doré"},
    },
    {
        "nom": "Chaise pliante housse blanche",
        "categorie": "mobilier",
        "unite_facturation": "unite",
        "prix_unitaire": 1_000,
        "attributs": {"style": "pliante avec housse"},
    },
    {
        "nom": "Menu Prestige buffet complet",
        "categorie": "restauration",
        "unite_facturation": "personne",
        "prix_unitaire": 15_000,
        "attributs": {},
    },
    {
        "nom": "Menu Standard",
        "categorie": "restauration",
        "unite_facturation": "personne",
        "prix_unitaire": 8_000,
        "attributs": {},
    },
    {
        "nom": "Cocktail dînatoire",
        "categorie": "restauration",
        "unite_facturation": "personne",
        "prix_unitaire": 5_000,
        "attributs": {},
    },
    {
        "nom": "Décoration florale premium",
        "categorie": "decoration",
        "unite_facturation": "forfait",
        "prix_unitaire": 500_000,
        "attributs": {},
    },
    {
        "nom": "Décoration thématique standard",
        "categorie": "decoration",
        "unite_facturation": "forfait",
        "prix_unitaire": 250_000,
        "attributs": {},
    },
    {
        "nom": "Sonorisation complète avec DJ",
        "categorie": "sonorisation",
        "unite_facturation": "forfait",
        "prix_unitaire": 400_000,
        "attributs": {},
    },
    {
        "nom": "Sonorisation standard",
        "categorie": "sonorisation",
        "unite_facturation": "forfait",
        "prix_unitaire": 200_000,
        "attributs": {},
    },
    {
        "nom": "Maître de cérémonie bilingue",
        "categorie": "personnel",
        "unite_facturation": "forfait",
        "prix_unitaire": 150_000,
        "attributs": {},
    },
    {
        "nom": "Maître de cérémonie standard",
        "categorie": "personnel",
        "unite_facturation": "forfait",
        "prix_unitaire": 80_000,
        "attributs": {},
    },
    {
        "nom": "Installation et logistique complète",
        "categorie": "logistique",
        "unite_facturation": "forfait",
        "prix_unitaire": 300_000,
        "attributs": {},
    },
]

# La règle de quantité reprend le vocabulaire déjà fixé dans le besoin
# (type_evenement, nombre_invites, duree_jours...) décrit dans DONNEES.md
LIGNES_PAR_DEFAUT_MARIAGE = [
    {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1},
    {"categorie": "mobilier", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
    {"categorie": "restauration", "base_calcul": "nombre_invites", "quantite_par_unite": 1},
    {"categorie": "decoration", "base_calcul": "forfait", "quantite_par_unite": 1},
    {"categorie": "sonorisation", "base_calcul": "forfait", "quantite_par_unite": 1},
    {"categorie": "personnel", "base_calcul": "forfait", "quantite_par_unite": 1},
    {"categorie": "logistique", "base_calcul": "forfait", "quantite_par_unite": 1},
]


def get_or_create_tenant(session: Session) -> Tenant:
    """Cherche le tenant par slug, le crée s'il n'existe pas encore"""
    tenant = session.query(Tenant).filter_by(slug=TENANT_SLUG).first()
    if tenant is not None:
        return tenant

    tenant = Tenant(nom=TENANT_NOM, slug=TENANT_SLUG, ville=TENANT_VILLE)
    session.add(tenant)
    session.flush()
    return tenant


def get_or_create_ressource(session: Session, tenant: Tenant, donnees: dict) -> Ressource:
    """Cherche une ressource par (tenant, nom), la crée ou met à jour ses champs"""
    ressource = (
        session.query(Ressource)
        .filter_by(tenant_id=tenant.id, nom=donnees["nom"])
        .first()
    )
    if ressource is None:
        ressource = Ressource(tenant_id=tenant.id, nom=donnees["nom"])
        session.add(ressource)

    ressource.categorie = donnees["categorie"]
    ressource.unite_facturation = donnees["unite_facturation"]
    ressource.prix_unitaire = donnees["prix_unitaire"]
    ressource.attributs = donnees["attributs"]
    ressource.actif = True
    return ressource


def get_or_create_modele_mariage(session: Session, tenant: Tenant) -> ModeleEvenement:
    """Cherche le modèle d'événement Mariage par (tenant, nom), le crée ou le met à jour"""
    modele = (
        session.query(ModeleEvenement)
        .filter_by(tenant_id=tenant.id, nom="Mariage")
        .first()
    )
    if modele is None:
        modele = ModeleEvenement(tenant_id=tenant.id, nom="Mariage")
        session.add(modele)

    modele.description = "Modèle de quantités par défaut pour un mariage"
    modele.lignes_par_defaut = LIGNES_PAR_DEFAUT_MARIAGE
    return modele


def get_or_create_utilisateur_gestionnaire(session: Session, tenant: Tenant) -> tuple[Utilisateur, bool]:
    """Cherche le gestionnaire par (tenant, email), le crée s'il n'existe pas.

    Ne touche jamais au mot de passe d'un utilisateur déjà existant.
    Retourne (utilisateur, a_ete_cree).
    """
    utilisateur = (
        session.query(Utilisateur)
        .filter_by(tenant_id=tenant.id, email=EMAIL_GESTIONNAIRE)
        .first()
    )
    if utilisateur is not None:
        return utilisateur, False

    utilisateur = Utilisateur(
        tenant_id=tenant.id,
        email=EMAIL_GESTIONNAIRE,
        mot_de_passe_hache=hash_mot_de_passe(MOT_DE_PASSE_DEMO),
        nom=NOM_GESTIONNAIRE,
    )
    session.add(utilisateur)
    return utilisateur, True


def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        tenant = get_or_create_tenant(session)

        for donnees_ressource in RESSOURCES:
            get_or_create_ressource(session, tenant, donnees_ressource)

        get_or_create_modele_mariage(session, tenant)

        _, utilisateur_cree = get_or_create_utilisateur_gestionnaire(session, tenant)

        session.commit()

    print(f"Tenant « {TENANT_NOM} » (slug={TENANT_SLUG}) : {len(RESSOURCES)} ressources, modèle Mariage à jour.")
    if utilisateur_cree:
        print(f"Gestionnaire créé — email: {EMAIL_GESTIONNAIRE}  mot de passe: {MOT_DE_PASSE_DEMO}")
        print("Ces identifiants sont aussi consignés dans data/seed/README.md.")
    else:
        print(f"Gestionnaire déjà présent ({EMAIL_GESTIONNAIRE}), mot de passe inchangé.")


if __name__ == "__main__":
    main()
