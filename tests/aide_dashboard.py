"""Installation partagée des tests d'écran du tableau de bord.

Ce fichier n'est pas un module de tests (pas de préfixe test_, rien n'y est
collecté) : il porte l'installation dont les trois écrans ont besoin, pour ne
pas la recopier dans chaque fichier.

Les écrans exigent un gestionnaire déjà connecté. Plutôt que de rejouer le
formulaire de connexion à chaque test, le tenant_id et l'utilisateur sont posés
directement en session avant le premier rendu : le chemin de connexion, lui,
est couvert par tests/test_dashboard_connexion.py.
"""
from datetime import datetime
from pathlib import Path

from html import unescape

from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from src.auth.hachage import hash_mot_de_passe
from src.auth.types import UtilisateurContexte
from src.db.models import (
    ETAT_COMPLETE,
    ETAT_EN_COURS,
    Demande,
    Devis,
    ModeleEvenement,
    Prospect,
    Ressource,
    Tenant,
    Utilisateur,
)

CHEMIN_APP = str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py")

EMAIL_GESTIONNAIRE = "gestionnaire@etoile.com"
MOT_DE_PASSE = "Etoile-Demo-2026"
NOM_GESTIONNAIRE = "Alice Mbarga"

RESSOURCES_DE_TEST = [
    ("Salle des fêtes Le Bastos", "salle", "jour", 350_000, {"capacite": 300, "quartier": "Bastos"}),
    ("Chaise bâchée blanche", "mobilier", "unite", 500, {"style": "Housse et nœud inclus"}),
    ("Menu complet invité", "restauration", "personne", 7_500, {}),
]

BESOIN_MARIAGE_250 = {
    "type_evenement": "mariage",
    "date_evenement": "2026-12-12",
    "ville": "Yaoundé",
    "quartier_souhaite": "Bastos",
    "nombre_invites": 250,
    "duree_jours": 1,
}

LIGNES_FIGEES = [
    {
        "designation": "Salle des fêtes Le Bastos",
        "quantite": 1,
        "prix_unitaire": 350_000,
        "montant": 350_000,
        "ressource_id": "salle-1",
    },
    {
        "designation": "Menu complet invité",
        "quantite": 250,
        "prix_unitaire": 7_500,
        "montant": 1_875_000,
        "ressource_id": "menu-1",
    },
]


def installer_tenant(
    session: Session,
    slug: str = "etoile",
    nom: str = "Événements Étoile",
    avec_catalogue: bool = True,
) -> Tenant:
    """Crée une entreprise cliente, son gestionnaire et son catalogue"""
    tenant = Tenant(nom=nom, slug=slug, ville="Yaoundé", coordonnees="671234567, Bastos")
    session.add(tenant)
    session.flush()
    session.add(
        Utilisateur(
            tenant_id=tenant.id,
            email=f"gestionnaire@{slug}.com",
            mot_de_passe_hache=hash_mot_de_passe(MOT_DE_PASSE),
            nom=NOM_GESTIONNAIRE if slug == "etoile" else f"Gestionnaire {slug}",
        )
    )
    if avec_catalogue:
        session.add_all(
            Ressource(
                tenant_id=tenant.id,
                nom=nom_ressource,
                categorie=categorie,
                unite_facturation=unite,
                prix_unitaire=prix,
                attributs=attributs,
            )
            for nom_ressource, categorie, unite, prix, attributs in RESSOURCES_DE_TEST
        )
        session.add(
            ModeleEvenement(
                tenant_id=tenant.id,
                nom="Mariage",
                lignes_par_defaut=[
                    {"categorie": "salle", "base_calcul": "duree_jours", "quantite_par_unite": 1}
                ],
            )
        )
    session.commit()
    return tenant


def creer_prospect(
    session: Session,
    tenant: Tenant,
    date_creation: datetime,
    nom: str = "Sylvie Nkoa",
    telephone: str = "699001122",
    email: str | None = "sylvie@example.cm",
    consentement_contact: bool = True,
) -> Prospect:
    """Crée une fiche prospect seule, sans demande.

    Un prospect peut exister sans aucune demande : le formulaire de
    coordonnées est rempli avant que la conversation n'aboutisse. L'écran des
    prospects doit savoir montrer ce cas, d'où ce helper séparé de
    creer_demande, qui lui en crée toujours une.
    """
    prospect = Prospect(
        tenant_id=tenant.id,
        nom=nom,
        telephone=telephone,
        email=email,
        consentement_contact=consentement_contact,
        date_creation=date_creation,
    )
    session.add(prospect)
    session.commit()
    return prospect


def creer_demande(
    session: Session,
    tenant: Tenant,
    date_creation: datetime,
    besoin: dict | None = None,
    nom_prospect: str = "Sylvie Nkoa",
    telephone: str = "699001122",
    total_devis: int | None = None,
    consentement_contact: bool = True,
    besoins_hors_catalogue: str | None = None,
    commentaire: str | None = None,
    prospect: Prospect | None = None,
) -> Demande:
    """Crée une demande, son prospect, et son devis si un total est demandé.

    Les lignes sont écrites directement pour maîtriser les dates, ce que les
    fonctions de production ne permettent pas : le chemin réel, lui, est
    couvert par tests/test_canaux_streamlit_prospect.py.

    Passer un prospect existant (par exemple demande_precedente.prospect)
    simule un même prospect qui revient (voir D47) : aucune nouvelle ligne
    prospect n'est créée, nom_prospect/telephone/consentement_contact sont
    alors ignorés.
    """
    if prospect is None:
        prospect = creer_prospect(
            session,
            tenant,
            date_creation,
            nom=nom_prospect,
            telephone=telephone,
            consentement_contact=consentement_contact,
        )

    demande = Demande(
        tenant_id=tenant.id,
        canal="streamlit",
        prospect_id=prospect.id,
        etat=ETAT_COMPLETE if total_devis is not None else ETAT_EN_COURS,
        besoin=besoin if besoin is not None else BESOIN_MARIAGE_250,
        besoins_hors_catalogue=besoins_hors_catalogue,
        commentaire=commentaire,
        date_creation=date_creation,
    )
    session.add(demande)
    session.flush()

    if total_devis is not None:
        session.add(
            Devis(
                tenant_id=tenant.id,
                demande_id=demande.id,
                lignes=LIGNES_FIGEES,
                total=total_devis,
                date_emission=date_creation,
            )
        )
    session.commit()
    return demande


def lancer_ecran_connecte(
    tenant_id: str, ecran: str | None = None, nom_gestionnaire: str = NOM_GESTIONNAIRE
) -> AppTest:
    """Rend le tableau de bord avec un gestionnaire déjà connecté"""
    app = AppTest.from_file(CHEMIN_APP, default_timeout=30)
    app.session_state["tenant_id"] = tenant_id
    app.session_state["utilisateur"] = UtilisateurContexte(
        id="utilisateur-de-test",
        tenant_id=tenant_id,
        email=EMAIL_GESTIONNAIRE,
        nom=nom_gestionnaire,
    )
    if ecran is not None:
        app.session_state["ecran"] = ecran
    return app.run()


def texte_affiche(ecran: AppTest) -> str:
    """Tout le texte rendu, entités HTML retraduites.

    Attention en cherchant une absence : la feuille de style est injectée par
    st.markdown, elle fait donc partie de ce texte. Une assertion d'absence
    doit viser une donnée (un nom, un montant), jamais un mot qui pourrait
    figurer dans du CSS.
    """
    return unescape("\n".join(element.value for element in ecran.markdown))


def cliquer(ecran: AppTest, cle: str) -> AppTest:
    """Clique le bouton portant cette clé et rend l'écran suivant"""
    return next(bouton for bouton in ecran.button if bouton.key == cle).click().run()
