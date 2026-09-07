"""Demandes et devis de démonstration pour un tenant déjà provisionné.

Séparé de seed.py et de ajouter_tenant.py, qui provisionnent des entreprises
(profil, catalogue, gestionnaire) : injecter des demandes fictives dans
l'espace d'un vrai client serait une pollution (voir D25). Ce script est lancé
à la main, par l'opérateur, sur le tenant de son choix.

Les montants ne sont pas inventés : chaque devis passe par le vrai chemin de
production — enregistrement du prospect, ouverture de la demande, chiffrage sur
le catalogue réel du tenant, émission du devis. Un total de démonstration est
donc un total que le moteur produirait pour ce besoin (D01).

Usage (depuis la racine du projet, avec DATABASE_URL renseigné dans .env) :
    uv run python data/seed/demonstration.py etoile
    uv run python data/seed/demonstration.py etoile --force
"""
import argparse
import os
import sys
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker

from src.canaux.demande import actualiser_besoin, emettre_devis, ouvrir_demande
from src.canaux.prospect import enregistrer_prospect
from src.canaux.tenant import resoudre_tenant
from src.canaux.types import TenantIndisponible
from src.catalogue.provisionnement import NOM_MODELE_MARIAGE
from src.catalogue.ressources import charger_modele_evenement, charger_ressources_actives
from src.consultation.demandes import compter_demandes_du_tenant
from src.db.models import Demande, Devis, Prospect
from src.extraction.types import Besoin
from src.orchestration.parcours import chiffrer_pour_besoin, resoudre_candidats
from src.presentation.montant import formater_montant

CANAL = "streamlit"


@dataclass(frozen=True)
class ScenarioDemonstration:
    """Une demande de démonstration, telle qu'un prospect l'aurait laissée"""

    nom_prospect: str
    telephone: str
    email: str | None
    consentement_contact: bool
    mois_de_recul: int
    jour: int
    besoin: Besoin
    chiffree: bool


def _mariage(
    nombre_invites: int,
    quartier: str,
    duree_jours: int = 1,
    date_evenement: str = "2027-06-12",
    budget_declare: int | None = None,
) -> Besoin:
    """Besoin d'un mariage complet, le seul type d'événement de la v1 (D07)"""
    return Besoin(
        type_evenement="mariage",
        date_evenement=date_evenement,
        ville="Yaoundé",
        quartier_souhaite=quartier,
        nombre_invites=nombre_invites,
        duree_jours=duree_jours,
        budget_declare=budget_declare,
    )


# Invités répartis sur les quatre tranches d'invités du tableau de bord, dates
# étalées sur cinq mois pour que le sélecteur de période ait de la matière, et
# deux conversations laissées en cours pour que les deux statuts se voient.
SCENARIOS = (
    ScenarioDemonstration(
        nom_prospect="Sylvie Nkoa",
        telephone="699112233",
        email="sylvie.nkoa@example.cm",
        consentement_contact=True,
        mois_de_recul=0,
        jour=4,
        besoin=_mariage(250, "Bastos", date_evenement="2027-12-12"),
        chiffree=True,
    ),
    ScenarioDemonstration(
        nom_prospect="Roger Tchoumi",
        telephone="677445566",
        email="roger.tchoumi@example.cm",
        consentement_contact=True,
        mois_de_recul=0,
        jour=2,
        besoin=_mariage(90, "Nsimeyong", date_evenement="2027-10-18"),
        chiffree=True,
    ),
    ScenarioDemonstration(
        nom_prospect="Aminatou Bello",
        telephone="655778899",
        email=None,
        consentement_contact=True,
        mois_de_recul=1,
        jour=24,
        besoin=_mariage(400, "Odza", duree_jours=2, date_evenement="2028-02-20"),
        chiffree=False,
    ),
    ScenarioDemonstration(
        nom_prospect="Jean-Paul Etoundi",
        telephone="691223344",
        email="jp.etoundi@example.cm",
        consentement_contact=True,
        mois_de_recul=1,
        jour=12,
        besoin=_mariage(120, "Mfandena", date_evenement="2027-11-07"),
        chiffree=True,
    ),
    ScenarioDemonstration(
        nom_prospect="Estelle Ngo Bell",
        telephone="698334455",
        email="estelle.ngobell@example.cm",
        consentement_contact=False,
        mois_de_recul=2,
        jour=19,
        besoin=_mariage(600, "Biyem-Assi", duree_jours=2, date_evenement="2027-12-05"),
        chiffree=True,
    ),
    ScenarioDemonstration(
        nom_prospect="Patrick Abena",
        telephone="676556677",
        email=None,
        consentement_contact=True,
        mois_de_recul=3,
        jour=29,
        besoin=_mariage(320, "Bastos", date_evenement="2028-01-10", budget_declare=3_000_000),
        chiffree=True,
    ),
    ScenarioDemonstration(
        nom_prospect="Bertrand Kamdem",
        telephone="694667788",
        email=None,
        consentement_contact=False,
        mois_de_recul=4,
        jour=14,
        besoin=_mariage(45, "Odza", date_evenement="2027-08-23"),
        chiffree=True,
    ),
    # Conversation interrompue avant que le nombre d'invités soit connu : la
    # demande reste relançable par le commercial, et n'entre dans aucune
    # tranche du tableau de bord.
    ScenarioDemonstration(
        nom_prospect="Clarisse Ondoa",
        telephone="681778899",
        email="clarisse.ondoa@example.cm",
        consentement_contact=True,
        mois_de_recul=0,
        jour=6,
        besoin=Besoin(type_evenement="mariage", ville="Yaoundé"),
        chiffree=False,
    ),
)


def main() -> None:
    arguments = _lire_arguments()

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    fabrique_de_sessions = sessionmaker(bind=create_engine(database_url))
    with fabrique_de_sessions() as session:
        resolution = resoudre_tenant(session, arguments.slug)
        if isinstance(resolution, TenantIndisponible):
            raise SystemExit(
                f"Tenant « {arguments.slug} » indisponible ({resolution.raison}). "
                "Lance d'abord data/seed/seed.py."
            )
        tenant = resolution.tenant

        deja_presentes = compter_demandes_du_tenant(session, tenant.id)
        if deja_presentes and not arguments.force:
            raise SystemExit(
                f"« {tenant.nom} » a déjà {deja_presentes} demande(s). "
                "Relance avec --force pour en ajouter quand même."
            )

        catalogue = charger_ressources_actives(session, tenant.id)
        modele = charger_modele_evenement(session, tenant.id, NOM_MODELE_MARIAGE)
        if not catalogue or modele is None:
            raise SystemExit(
                f"« {tenant.nom} » n'a pas de catalogue ou pas de modèle "
                f"{NOM_MODELE_MARIAGE} : rien à chiffrer."
            )

        aujourdhui = date.today()
        for scenario in SCENARIOS:
            total = _creer_demande_de_demonstration(
                session, tenant.id, scenario, catalogue, modele, aujourdhui
            )
            etat = formater_montant(total) if total is not None else "sans estimation"
            print(f"  {scenario.nom_prospect:22} {etat}")

    print(f"\n{len(SCENARIOS)} demandes de démonstration ajoutées à « {tenant.nom} ».")
    print("Tableau de bord : uv run streamlit run dashboard/app.py")


def _creer_demande_de_demonstration(
    session: Session,
    tenant_id: str,
    scenario: ScenarioDemonstration,
    catalogue: list,
    modele: list,
    aujourdhui: date,
) -> int | None:
    """Rejoue une conversation complète et renvoie le total du devis, si émis"""
    prospect = enregistrer_prospect(
        session,
        tenant_id,
        nom=scenario.nom_prospect,
        telephone=scenario.telephone,
        email=scenario.email,
        consentement_contact=scenario.consentement_contact,
    )
    demande = ouvrir_demande(
        session, tenant_id, canal=CANAL, prospect_id=prospect.id, besoin={}
    )

    besoin = scenario.besoin
    if scenario.chiffree:
        besoin = _choisir_une_option_par_categorie(besoin, catalogue, modele)
    actualiser_besoin(session, tenant_id, demande.id, _en_dictionnaire(besoin))

    total = None
    if scenario.chiffree:
        resultat = chiffrer_pour_besoin(besoin, catalogue, modele)
        if resultat.lignes:
            emettre_devis(session, tenant_id, demande.id, resultat)
            total = resultat.total

    _antidater(
        session,
        tenant_id,
        demande.id,
        prospect.id,
        _recul_de_mois(aujourdhui, scenario.mois_de_recul, scenario.jour),
    )
    return total


def _choisir_une_option_par_categorie(
    besoin: Besoin, catalogue: list, modele: list
) -> Besoin:
    """Retient la première option de chaque catégorie, comme le ferait un prospect.

    Le choix des ressources reste celui du prospect dans le produit (D03) : ici
    on en simule un, on ne laisse pas le moteur décider tout seul.
    """
    candidats = resoudre_candidats(besoin, catalogue, modele)
    choisies = tuple(options[0].id for options in candidats.values() if options)
    return replace(besoin, ressources_choisies=choisies)


def _en_dictionnaire(besoin: Besoin) -> dict:
    """Besoin tel qu'il est stocké dans Demande.besoin"""
    return asdict(besoin)


def _recul_de_mois(reference: date, mois: int, jour: int) -> datetime:
    """Date d'il y a « mois » mois, au jour demandé, ramené au mois s'il n'existe pas"""
    annee = reference.year
    numero_mois = reference.month - mois
    while numero_mois < 1:
        numero_mois += 12
        annee -= 1
    jour_valide = min(jour, 28)
    return datetime(annee, numero_mois, jour_valide, 10, 30)


def _antidater(
    session: Session, tenant_id: str, demande_id: str, prospect_id: str, quand: datetime
) -> None:
    """Recule les dates de la demande, de son prospect et de son devis.

    Les fonctions de production datent tout de l'instant présent, ce qui est
    juste en usage réel mais donnerait un tableau de bord où tout serait
    arrivé le même jour. L'antidatage ne concerne que la démonstration et
    reste cantonné à ce script ; les requêtes filtrent le tenant comme
    partout ailleurs.
    """
    session.execute(
        update(Prospect)
        .where(Prospect.id == prospect_id, Prospect.tenant_id == tenant_id)
        .values(date_creation=quand)
    )
    session.execute(
        update(Demande)
        .where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
        .values(date_creation=quand, date_modification=quand)
    )
    session.execute(
        update(Devis)
        .where(Devis.demande_id == demande_id, Devis.tenant_id == tenant_id)
        .values(date_emission=quand)
    )
    session.commit()


def _lire_arguments() -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("slug", help="Slug du tenant à peupler, par exemple etoile")
    analyseur.add_argument(
        "--force",
        action="store_true",
        help="Ajoute les demandes même si le tenant en a déjà",
    )
    return analyseur.parse_args()


if __name__ == "__main__":
    main()
