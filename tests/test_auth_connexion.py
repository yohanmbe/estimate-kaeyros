from sqlalchemy.orm import Session

from src.auth.connexion import connecter
from src.auth.hachage import hash_mot_de_passe
from src.auth.types import ConnexionEchouee, ConnexionReussie
from src.db.models import Tenant, Utilisateur

MOT_DE_PASSE = "Etoile-Demo-2026"


def creer_gestionnaire(session: Session, actif: bool = True) -> tuple[Tenant, Utilisateur]:
    tenant = Tenant(nom="Événements Étoile", slug="etoile")
    session.add(tenant)
    session.flush()
    utilisateur = Utilisateur(
        tenant_id=tenant.id,
        email="gestionnaire@etoile-events.cm",
        mot_de_passe_hache=hash_mot_de_passe(MOT_DE_PASSE),
        nom="Gestionnaire Étoile",
        actif=actif,
    )
    session.add(utilisateur)
    session.commit()
    return tenant, utilisateur


def test_email_et_mot_de_passe_corrects_etablit_la_connexion(session):
    tenant, utilisateur = creer_gestionnaire(session)

    resultat = connecter(session, "gestionnaire@etoile-events.cm", MOT_DE_PASSE)

    assert isinstance(resultat, ConnexionReussie)
    assert resultat.utilisateur.id == utilisateur.id
    assert resultat.utilisateur.tenant_id == tenant.id
    assert resultat.utilisateur.nom == "Gestionnaire Étoile"


def test_email_inconnu_est_refuse(session):
    creer_gestionnaire(session)

    resultat = connecter(session, "inconnu@ailleurs.cm", MOT_DE_PASSE)

    assert resultat == ConnexionEchouee(raison="identifiants_invalides")


def test_mot_de_passe_incorrect_est_refuse(session):
    creer_gestionnaire(session)

    resultat = connecter(session, "gestionnaire@etoile-events.cm", "mauvais-mot-de-passe")

    assert resultat == ConnexionEchouee(raison="identifiants_invalides")


def test_compte_desactive_est_refuse_meme_avec_le_bon_mot_de_passe(session):
    creer_gestionnaire(session, actif=False)

    resultat = connecter(session, "gestionnaire@etoile-events.cm", MOT_DE_PASSE)

    assert resultat == ConnexionEchouee(raison="compte_inactif")


def test_connexion_reussie_met_a_jour_la_derniere_connexion(session):
    tenant, utilisateur = creer_gestionnaire(session)
    assert utilisateur.derniere_connexion is None

    resultat = connecter(session, "gestionnaire@etoile-events.cm", MOT_DE_PASSE)

    assert isinstance(resultat, ConnexionReussie)
    assert utilisateur.derniere_connexion is not None


def test_connexion_echouee_ne_modifie_pas_la_derniere_connexion(session):
    tenant, utilisateur = creer_gestionnaire(session)

    connecter(session, "gestionnaire@etoile-events.cm", "mauvais-mot-de-passe")

    assert utilisateur.derniere_connexion is None
