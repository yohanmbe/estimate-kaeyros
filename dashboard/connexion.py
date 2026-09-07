"""Écran de connexion du tableau de bord gestionnaire.

Vérifie l'email et le mot de passe puis établit le tenant_id en session
(voir CLAUDE.md, Multi-locataires). N'affiche et ne calcule aucun montant :
les écrans indicateurs, catalogue et demandes restent à construire (D18).

Lancement : streamlit run dashboard/connexion.py
"""
import sys
from pathlib import Path

import streamlit as st

# Permet de lancer ce fichier via « streamlit run » sans que la racine du
# projet soit déjà sur le sys.path (même besoin que src/canaux/streamlit_prospect.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.auth.connexion import connecter  # noqa: E402
from src.auth.types import ConnexionReussie, ResolutionConnexion  # noqa: E402
from src.db.session import ouvrir_session  # noqa: E402

MESSAGES_ECHEC = {
    "identifiants_invalides": (
        "L'adresse email ou le mot de passe est incorrect. "
        "Vérifiez vos identifiants et réessayez."
    ),
    "compte_inactif": "Ce compte a été désactivé. Contactez votre administrateur.",
}

# Palette Kaeyros : bleu #0f2a96 et orange #ff5f00, comme src/canaux/streamlit_prospect.py.
FEUILLE_DE_STYLE = """
<style>
:root{
  --bleu:#0f2a96; --bleu-fonce:#0a1f6f; --bleu-pale:#eaeefb;
  --orange:#ff5f00; --orange-texte:#d94f00;
  --encre:#101322; --gris:#5b6178; --trait:#e2e6f2;
  --surface:#ffffff; --fond:#f4f5fb;
  --rouge-texte:#7a1622; --rouge-pale:#fdecee; --rouge-trait:#f0aab3;
}

.stApp{
  background:
    radial-gradient(1300px 900px at 6% -10%, rgba(15,42,150,.14), transparent 62%),
    radial-gradient(1100px 780px at 104% 2%, rgba(255,95,0,.12), transparent 58%),
    var(--fond);
  background-attachment:fixed;
}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none;}
[data-testid="stHeader"]{background:transparent;}
.stMainBlockContainer, .block-container{max-width:430px;padding-top:4.2rem;}

.marque-connexion{text-align:center;margin-bottom:1.7rem;}
.marque-connexion__nom{font-size:1.75rem;font-weight:800;color:var(--encre);letter-spacing:-.01em;}
.marque-connexion__sous{font-size:.92rem;color:var(--orange-texte);font-weight:700;margin-top:.25rem;}

[class*="st-key-carte-connexion"]{background:var(--surface);border:1px solid var(--trait);
  border-radius:20px;padding:1.9rem 1.9rem 1.3rem;box-shadow:0 12px 34px rgba(16,19,34,.10);}

.stTextInput label{font-weight:600;color:var(--encre);font-size:.87rem;}
.stTextInput input{border-radius:10px;}

/* Bordure et fond rouges des champs quand la connexion vient d'échouer,
   sans dupliquer le formulaire : seule la clé du conteneur change. */
[class*="st-key-carte-connexion-erreur"] .stTextInput input{
  border-color:var(--rouge-trait) !important;background:var(--rouge-pale) !important;}

[class*="st-key-carte-connexion"] .stFormSubmitButton>button{background:var(--bleu);
  color:#fff;border:none;border-radius:10px;font-weight:700;padding:.65rem 0;width:100%;}
[class*="st-key-carte-connexion"] .stFormSubmitButton>button:hover{background:var(--bleu-fonce);color:#fff;}

.alerte-connexion{background:var(--rouge-pale);border:1px solid var(--rouge-trait);
  border-radius:12px;padding:.85rem 1.05rem;margin-bottom:1rem;color:var(--rouge-texte);
  font-size:.87rem;line-height:1.5;}
.alerte-connexion__titre{font-weight:700;margin-bottom:.2rem;}

.pied-connexion{text-align:center;margin-top:1.2rem;font-size:.85rem;color:var(--gris);}
.pied-connexion a{color:var(--bleu);font-weight:600;text-decoration:none;}
</style>
"""


def main() -> None:
    """Affiche la connexion, ou un écran de repli si déjà connecté"""
    st.set_page_config(page_title="Estimate — Espace professionnel", layout="centered")
    st.markdown(FEUILLE_DE_STYLE, unsafe_allow_html=True)

    if "utilisateur" in st.session_state:
        _afficher_ecran_connecte()
        return

    _afficher_ecran_connexion()


def _afficher_ecran_connexion() -> None:
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
        '<div class="pied-connexion">Pas encore de compte ? '
        '<a href="mailto:contact@estimate.cm">Contactez-nous</a></div>',
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


def _afficher_ecran_connecte() -> None:
    """Écran de repli en attendant les indicateurs, le catalogue et les demandes (D18)"""
    utilisateur = st.session_state.utilisateur
    st.markdown(f"### Bienvenue, {utilisateur.nom}")
    st.caption(f"Connecté en tant que {utilisateur.email}")
    if st.button("Se déconnecter"):
        st.session_state.pop("utilisateur", None)
        st.session_state.pop("tenant_id", None)
        st.rerun()


if __name__ == "__main__":
    main()
