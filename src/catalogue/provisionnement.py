"""Création ou mise à jour d'un tenant complet : profil, catalogue, modèle,
gestionnaire (voir D25 dans DECISIONS.md).

Partagé par data/seed/seed.py (le tenant de démonstration, codé en dur) et
data/seed/ajouter_tenant.py (un vrai client, décrit dans un fichier JSON) :
un seul chemin de code crée un tenant, qu'il s'agisse de démonstration ou
d'un client réel.

Idempotent comme le reste du seed : chaque entité est recherchée par sa clé
métier avant d'être créée ou mise à jour, jamais insérée à l'aveugle.
"""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.auth.hachage import hash_mot_de_passe
from src.db.models import ModeleEvenement, Ressource, Tenant, Utilisateur

NOM_MODELE_MARIAGE = "Mariage"


@dataclass(frozen=True)
class RessourceAProvisionner:
    """Une ligne de catalogue à créer ou mettre à jour pour un tenant"""

    nom: str
    categorie: str
    unite_facturation: str
    prix_unitaire: int
    attributs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LigneModeleAProvisionner:
    """Une entrée de lignes_par_defaut du modèle d'événement Mariage"""

    categorie: str
    base_calcul: str
    quantite_par_unite: int


@dataclass(frozen=True)
class GestionnaireAProvisionner:
    """Le compte du gestionnaire du tableau de bord pour ce tenant"""

    email: str
    nom: str
    mot_de_passe: str


@dataclass(frozen=True)
class ConfigurationTenant:
    """Tout ce qu'il faut pour qu'un tenant soit opérationnel dans le chat"""

    nom: str
    slug: str
    ville: str | None
    logo: str | None
    ressources: list[RessourceAProvisionner]
    modele_mariage: list[LigneModeleAProvisionner]
    gestionnaire: GestionnaireAProvisionner


def configuration_depuis_dict(donnees: dict) -> ConfigurationTenant:
    """Valide et convertit un dict brut (typiquement issu d'un fichier JSON).

    Signale par une erreur claire le premier champ obligatoire manquant,
    plutôt que de laisser remonter un KeyError sans contexte à l'opérateur
    qui remplit le fichier à la main.
    """
    for champ in ("nom", "slug", "ressources", "modele_mariage", "gestionnaire"):
        if champ not in donnees:
            raise ValueError(f"Champ obligatoire manquant dans la configuration : {champ}")

    gestionnaire = donnees["gestionnaire"]
    for champ in ("email", "nom", "mot_de_passe"):
        if champ not in gestionnaire:
            raise ValueError(f"Champ obligatoire manquant dans « gestionnaire » : {champ}")

    return ConfigurationTenant(
        nom=donnees["nom"],
        slug=donnees["slug"],
        ville=donnees.get("ville"),
        logo=donnees.get("logo"),
        ressources=[
            RessourceAProvisionner(
                nom=ressource["nom"],
                categorie=ressource["categorie"],
                unite_facturation=ressource["unite_facturation"],
                prix_unitaire=ressource["prix_unitaire"],
                attributs=ressource.get("attributs", {}),
            )
            for ressource in donnees["ressources"]
        ],
        modele_mariage=[
            LigneModeleAProvisionner(
                categorie=ligne["categorie"],
                base_calcul=ligne["base_calcul"],
                quantite_par_unite=ligne["quantite_par_unite"],
            )
            for ligne in donnees["modele_mariage"]
        ],
        gestionnaire=GestionnaireAProvisionner(
            email=gestionnaire["email"],
            nom=gestionnaire["nom"],
            mot_de_passe=gestionnaire["mot_de_passe"],
        ),
    )


def provisionner_tenant(session: Session, configuration: ConfigurationTenant) -> tuple[Tenant, bool]:
    """Crée ou met à jour le tenant, son catalogue, son modèle et son gestionnaire.

    Ne committe pas : à l'appelant de le faire une fois l'opération terminée,
    comme le fait déjà data/seed/seed.py.
    Retourne (tenant, gestionnaire_cree) : gestionnaire_cree distingue un
    compte tout juste créé (dont le mot de passe doit être communiqué) d'un
    compte déjà existant (dont le mot de passe n'est jamais modifié ici).
    """
    tenant = _get_or_create_tenant(session, configuration)

    for ressource in configuration.ressources:
        _get_or_create_ressource(session, tenant, ressource)

    _get_or_create_modele_mariage(session, tenant, configuration.modele_mariage)

    _, gestionnaire_cree = _get_or_create_gestionnaire(session, tenant, configuration.gestionnaire)

    return tenant, gestionnaire_cree


def _get_or_create_tenant(session: Session, configuration: ConfigurationTenant) -> Tenant:
    """Cherche le tenant par slug, le crée ou met à jour ses champs descriptifs"""
    tenant = session.query(Tenant).filter_by(slug=configuration.slug).first()
    if tenant is None:
        tenant = Tenant(slug=configuration.slug)
        session.add(tenant)

    tenant.nom = configuration.nom
    tenant.ville = configuration.ville
    tenant.logo = configuration.logo
    session.flush()
    return tenant


def _get_or_create_ressource(
    session: Session, tenant: Tenant, ressource: RessourceAProvisionner
) -> Ressource:
    """Cherche une ressource par (tenant, nom), la crée ou met à jour ses champs"""
    ligne = session.query(Ressource).filter_by(tenant_id=tenant.id, nom=ressource.nom).first()
    if ligne is None:
        ligne = Ressource(tenant_id=tenant.id, nom=ressource.nom)
        session.add(ligne)

    ligne.categorie = ressource.categorie
    ligne.unite_facturation = ressource.unite_facturation
    ligne.prix_unitaire = ressource.prix_unitaire
    ligne.attributs = ressource.attributs
    ligne.actif = True
    return ligne


def _get_or_create_modele_mariage(
    session: Session, tenant: Tenant, lignes: list[LigneModeleAProvisionner]
) -> ModeleEvenement:
    """Cherche le modèle Mariage du tenant, le crée ou met à jour ses lignes"""
    modele = (
        session.query(ModeleEvenement)
        .filter_by(tenant_id=tenant.id, nom=NOM_MODELE_MARIAGE)
        .first()
    )
    if modele is None:
        modele = ModeleEvenement(tenant_id=tenant.id, nom=NOM_MODELE_MARIAGE)
        session.add(modele)

    modele.description = "Modèle de quantités par défaut pour un mariage"
    modele.lignes_par_defaut = [
        {
            "categorie": ligne.categorie,
            "base_calcul": ligne.base_calcul,
            "quantite_par_unite": ligne.quantite_par_unite,
        }
        for ligne in lignes
    ]
    return modele


def _get_or_create_gestionnaire(
    session: Session, tenant: Tenant, gestionnaire: GestionnaireAProvisionner
) -> tuple[Utilisateur, bool]:
    """Cherche le gestionnaire par (tenant, email), le crée s'il n'existe pas.

    Ne touche jamais au mot de passe d'un utilisateur déjà existant : relancer
    le script après un changement de mot de passe côté client ne l'écraserait
    pas silencieusement.
    """
    utilisateur = (
        session.query(Utilisateur)
        .filter_by(tenant_id=tenant.id, email=gestionnaire.email)
        .first()
    )
    if utilisateur is not None:
        return utilisateur, False

    utilisateur = Utilisateur(
        tenant_id=tenant.id,
        email=gestionnaire.email,
        mot_de_passe_hache=hash_mot_de_passe(gestionnaire.mot_de_passe),
        nom=gestionnaire.nom,
    )
    session.add(utilisateur)
    return utilisateur, True
