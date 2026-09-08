"""Tableau de bord du gestionnaire : point d'entrée unique.

Lancement : streamlit run dashboard/app.py

Cet écran règle la page, charge la feuille de style, garde la porte, puis
aiguille vers l'un des trois écrans. Le tenant_id vient uniquement de la
session établie à la connexion : jamais d'un paramètre d'URL, jamais d'une
liste déroulante (voir CLAUDE.md, Multi-locataires). Sans lui, rien ne
s'affiche que le formulaire de connexion.

Aucune mise en cache Streamlit ici, volontairement : un cache dont la clé
oublierait le tenant_id servirait les chiffres d'une entreprise à une autre.
Les requêtes sont petites, c'est un choix de sécurité et non de performance.
"""
import base64
import sys
from html import escape
from pathlib import Path

import streamlit as st

# Permet de lancer ce fichier via « streamlit run » sans que la racine du
# projet soit déjà sur le sys.path (même besoin que src/canaux/streamlit_prospect.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.catalogue import afficher_catalogue  # noqa: E402
from dashboard.connexion import afficher_connexion  # noqa: E402
from dashboard.demandes import afficher_demandes  # noqa: E402
from dashboard.style import FEUILLE_DE_STYLE, STYLE_CONNEXION  # noqa: E402
from dashboard.tableau_de_bord import afficher_tableau_de_bord  # noqa: E402
from src.auth.types import UtilisateurContexte  # noqa: E402
from src.canaux.tenant import charger_tenant  # noqa: E402
from src.canaux.types import TenantContexte  # noqa: E402
from src.db.session import ouvrir_session  # noqa: E402

# Le même dossier d'assets que le chat du prospect : déposer logo.png ou
# logo.svg y remplace la pastille de repli, sans toucher au code.
DOSSIER_ASSETS = Path(__file__).resolve().parents[1] / "src" / "canaux" / "assets"
FORMATS_LOGO_ACCEPTES = {".svg": "image/svg+xml", ".png": "image/png"}

ECRAN_PAR_DEFAUT = "tableau_de_bord"

# Ordre d'affichage de la navigation, son icône, et l'écran associé à chaque
# entrée. L'icône est un simple repère visuel de destination, pas une
# nomenclature à interpréter.
ECRANS = {
    "tableau_de_bord": ("", "Tableau de bord", afficher_tableau_de_bord),
    "catalogue": ("", "Catalogue", afficher_catalogue),
    "demandes": ("", "Demandes", afficher_demandes),
}


def main() -> None:
    """Aiguille vers la connexion ou vers l'écran demandé"""
    st.set_page_config(page_title="Estimate — Espace professionnel", layout="wide")
    st.markdown(FEUILLE_DE_STYLE, unsafe_allow_html=True)

    if "tenant_id" not in st.session_state:
        st.markdown(STYLE_CONNEXION, unsafe_allow_html=True)
        afficher_connexion()
        return

    tenant = _charger_tenant_de_la_session()
    if tenant is None:
        _deconnecter()
        return

    utilisateur = st.session_state.utilisateur
    nom_ecran = st.session_state.get("ecran", ECRAN_PAR_DEFAUT)
    _afficher_barre_laterale(tenant, utilisateur, nom_ecran)
    ECRANS[nom_ecran][2](tenant, utilisateur)


def _charger_tenant_de_la_session() -> TenantContexte | None:
    """Charge l'entreprise du gestionnaire connecté, None si elle a disparu"""
    with ouvrir_session() as session:
        return charger_tenant(session, st.session_state.tenant_id)


def _afficher_barre_laterale(
    tenant: TenantContexte, utilisateur: UtilisateurContexte, nom_ecran: str
) -> None:
    """Marque, navigation, entreprise connectée et déconnexion"""
    with st.sidebar:
        st.markdown(
            f'<div class="marque">{_logo_marque()}'
            f'<span class="marque__nom">Estimate</span></div>'
            f'<div class="marque__sous">Espace professionnel</div>',
            unsafe_allow_html=True,
        )
        _afficher_navigation(nom_ecran)
        _afficher_pied_lateral(tenant, utilisateur)


def _afficher_navigation(nom_ecran: str) -> None:
    """Un bouton par écran, celui en cours porte l'état actif.

    L'état vit dans la clé du conteneur et non dans le HTML : la feuille de
    style s'occupe seule de distinguer l'écran courant. Chaque bouton porte une
    icône et une flèche de destination (posée par le CSS) : le repère visuel
    qui dit « ceci est une page, pas juste un mot » ne doit pas dépendre du survol.
    """
    for nom, (icone, libelle, _) in ECRANS.items():
        actif = nom == nom_ecran
        with st.container(key=f"lien-nav-actif-{nom}" if actif else f"lien-nav-{nom}"):
            if st.button(f"{icone}  {libelle}", key=f"nav-{nom}", use_container_width=True):
                _aller_a(nom)


def _afficher_pied_lateral(tenant: TenantContexte, utilisateur: UtilisateurContexte) -> None:
    """Entreprise connectée, gestionnaire, puis déconnexion"""
    st.markdown(
        f'<div class="pied-lateral">'
        f'<span class="pied-lateral__pastille">{escape(_initiales(tenant.nom))}</span>'
        f'<span class="pied-lateral__texte"><span class="pied-lateral__nom">{escape(tenant.nom)}</span>'
        f'<span class="pied-lateral__meta">{escape(utilisateur.nom)}</span></span></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="deconnexion"):
        if st.button("Se déconnecter", key="deconnexion-bouton", use_container_width=True):
            _deconnecter()


def _aller_a(nom_ecran: str) -> None:
    """Change d'écran et oublie l'état propre à l'écran quitté"""
    st.session_state.ecran = nom_ecran
    st.session_state.pop("demande_ouverte", None)
    st.session_state.pop("ressource_en_edition", None)
    st.rerun()


def _deconnecter() -> None:
    """Efface le tenant_id et tout ce qui en dépend : rien ne doit survivre à la sortie"""
    for cle in (
        "utilisateur",
        "tenant_id",
        "ecran",
        "demande_ouverte",
        "ressource_en_edition",
    ):
        st.session_state.pop(cle, None)
    st.rerun()


def _initiales(nom: str) -> str:
    """Deux initiales du nom de l'entreprise, pour la pastille de la barre latérale"""
    mots = [mot for mot in nom.split() if mot]
    return "".join(mot[0].upper() for mot in mots[:2]) or "?"


def _logo_marque() -> str:
    """Balisage du logo si un fichier est présent, sinon la pastille de repli"""
    for suffixe, type_mime in FORMATS_LOGO_ACCEPTES.items():
        chemin = DOSSIER_ASSETS / f"logo{suffixe}"
        if chemin.is_file():
            contenu_encode = base64.b64encode(chemin.read_bytes()).decode()
            return (
                f'<img class="marque__logo" src="data:{type_mime};base64,{contenu_encode}"'
                ' alt="Logo">'
            )
    return '<span class="marque__pastille"></span>'


if __name__ == "__main__":
    main()
