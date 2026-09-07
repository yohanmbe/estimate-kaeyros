"""Écran de connexion piloté sans navigateur (streamlit.testing), sans réseau ni Postgres"""
from pathlib import Path

from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from src.auth.hachage import hash_mot_de_passe
from src.db.models import Tenant, Utilisateur

CHEMIN_ECRAN = str(Path(__file__).resolve().parents[1] / "dashboard" / "connexion.py")

MOT_DE_PASSE = "Etoile-Demo-2026"
EMAIL = "gestionnaire@etoile-events.cm"


def creer_gestionnaire(session: Session, actif: bool = True) -> tuple[Tenant, Utilisateur]:
    tenant = Tenant(nom="Événements Étoile", slug="etoile")
    session.add(tenant)
    session.flush()
    utilisateur = Utilisateur(
        tenant_id=tenant.id,
        email=EMAIL,
        mot_de_passe_hache=hash_mot_de_passe(MOT_DE_PASSE),
        nom="Gestionnaire Étoile",
        actif=actif,
    )
    session.add(utilisateur)
    session.commit()
    return tenant, utilisateur


def lancer_ecran() -> AppTest:
    return AppTest.from_file(CHEMIN_ECRAN, default_timeout=30).run()


def se_connecter(ecran: AppTest, email: str, mot_de_passe: str) -> AppTest:
    ecran.text_input[0].set_value(email)
    ecran.text_input[1].set_value(mot_de_passe)
    return ecran.button[0].click().run()


def test_ecran_sans_saisie_naffiche_aucune_alerte(base_branchee):
    ecran = lancer_ecran()

    assert ecran.error == []
    assert "Estimate" in "\n".join(t.value for t in ecran.markdown)


def test_bons_identifiants_etablit_le_tenant_id_en_session(base_branchee):
    tenant, _ = creer_gestionnaire(base_branchee)

    ecran = se_connecter(lancer_ecran(), EMAIL, MOT_DE_PASSE)

    assert ecran.session_state["tenant_id"] == tenant.id
    assert ecran.session_state["utilisateur"].email == EMAIL


def test_bons_identifiants_affiche_le_nom_du_gestionnaire(base_branchee):
    creer_gestionnaire(base_branchee)

    ecran = se_connecter(lancer_ecran(), EMAIL, MOT_DE_PASSE)

    texte = "\n".join(t.value for t in ecran.markdown)
    assert "Gestionnaire Étoile" in texte


def test_mauvais_mot_de_passe_naffiche_pas_le_tableau_de_bord(base_branchee):
    creer_gestionnaire(base_branchee)

    ecran = se_connecter(lancer_ecran(), EMAIL, "mot-de-passe-errone")

    assert "tenant_id" not in ecran.session_state
    texte = "\n".join(t.value for t in ecran.markdown)
    assert "Connexion refusée" in texte
    assert "incorrect" in texte


def test_mauvais_mot_de_passe_naffiche_jamais_le_mot_de_passe_saisi(base_branchee):
    creer_gestionnaire(base_branchee)

    ecran = se_connecter(lancer_ecran(), EMAIL, "mot-de-passe-errone")

    texte = "\n".join(t.value for t in ecran.markdown)
    assert "mot-de-passe-errone" not in texte


def test_email_inconnu_affiche_le_meme_message_que_mauvais_mot_de_passe(base_branchee):
    creer_gestionnaire(base_branchee)

    ecran = se_connecter(lancer_ecran(), "inconnu@ailleurs.cm", MOT_DE_PASSE)

    texte = "\n".join(t.value for t in ecran.markdown)
    assert "incorrect" in texte


def test_compte_desactive_refuse_la_connexion(base_branchee):
    creer_gestionnaire(base_branchee, actif=False)

    ecran = se_connecter(lancer_ecran(), EMAIL, MOT_DE_PASSE)

    assert "tenant_id" not in ecran.session_state
    texte = "\n".join(t.value for t in ecran.markdown)
    assert "désactivé" in texte


def test_deconnexion_efface_le_tenant_id_de_la_session(base_branchee):
    creer_gestionnaire(base_branchee)
    ecran = se_connecter(lancer_ecran(), EMAIL, MOT_DE_PASSE)
    assert "tenant_id" in ecran.session_state

    ecran = ecran.button[0].click().run()

    assert "tenant_id" not in ecran.session_state
    assert "utilisateur" not in ecran.session_state
