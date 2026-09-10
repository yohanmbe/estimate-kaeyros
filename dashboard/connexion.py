"""Écran de connexion du tableau de bord gestionnaire (voir D18).

Vérifie l'email et le mot de passe puis établit le tenant_id en session, dont
toutes les requêtes des écrans dépendent (voir CLAUDE.md, Multi-locataires).
N'affiche et ne calcule aucun montant.

Appelé par dashboard/app.py, qui règle la page et charge la feuille de style :
cet écran ne fait que le formulaire et la vérification des identifiants.
"""
import streamlit as st

from src.auth.connexion import connecter
from src.auth.types import ConnexionReussie, ResolutionConnexion
from src.db.session import ouvrir_session

MESSAGES_ECHEC = {
    "identifiants_invalides": (
        "L'adresse email ou le mot de passe est incorrect. "
        "Vérifiez vos identifiants et réessayez."
    ),
    "compte_inactif": "Ce compte a été désactivé. Contactez votre administrateur.",
}


def afficher_connexion() -> None:
    """Formulaire de connexion, avec l'alerte d'échec s'il y en a une à montrer"""
    st.markdown(
        """<div class="marque-connexion">
          <div class="marque-connexion__nom">Estimate</div>
          <div class="marque-connexion__sous">Espace professionnel</div>
        </div>""",
        unsafe_allow_html=True,
    )

    erreur = st.session_state.pop("erreur_connexion", None)
    cle_carte = "carte-connexion-erreur" if erreur else "carte-connexion"

    with st.container(key=cle_carte):
        if erreur:
            st.markdown(
                '<div class="alerte-connexion">'
                '<div class="alerte-connexion__titre">Connexion refusée</div>'
                f"{erreur}</div>",
                unsafe_allow_html=True,
            )

        with st.form("formulaire-connexion", border=False):
            email = st.text_input("Adresse email", placeholder="vous@entreprise.cm")
            mot_de_passe = st.text_input(
                "Mot de passe", type="password", placeholder="••••••••"
            )
            soumis = st.form_submit_button("Se connecter", use_container_width=True)

    if soumis:
        _traiter_soumission(email, mot_de_passe)
        st.rerun()

    st.markdown(
        '<div class="pied-connexion">Un probléme avec votre compte ? '
        '<a href="https://kaeyros-analytics.com/fr/contact-us" target="_blank" '
        'rel="noopener">Contactez-nous</a></div>',
        unsafe_allow_html=True,
    )


def _traiter_soumission(email: str, mot_de_passe: str) -> None:
    """Tente la connexion et prépare le prochain rendu selon le résultat"""
    with ouvrir_session() as session:
        resultat = connecter(session, email.strip(), mot_de_passe)
        if isinstance(resultat, ConnexionReussie):
            session.commit()
            _etablir_session_connectee(resultat)
            return
        _memoriser_echec(resultat)


def _etablir_session_connectee(resultat: ConnexionReussie) -> None:
    """Établit le tenant_id de la session : toute requête du tableau de bord en dépend"""
    st.session_state.tenant_id = resultat.utilisateur.tenant_id
    st.session_state.utilisateur = resultat.utilisateur


def _memoriser_echec(resultat: ResolutionConnexion) -> None:
    """Garde le message d'échec pour le prochain rendu, jamais le mot de passe soumis"""
    st.session_state.erreur_connexion = MESSAGES_ECHEC[resultat.raison]
