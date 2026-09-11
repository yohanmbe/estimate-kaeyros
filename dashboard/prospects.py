"""Écran des prospects : le carnet d'adresses du gestionnaire (voir D49).

L'écran des demandes entre par la demande, celui-ci entre par la personne.
C'est le même fonds de données lu dans l'autre sens : un prospect appelle, le
gestionnaire tape son numéro et retrouve tout ce que cette personne a déjà
demandé.

En lecture seule, comme l'écran des demandes : une fiche prospect n'est jamais
modifiée ici, pas même pour corriger une faute de frappe — la fiche est ce que
le prospect a saisi lui-même, et une visite suivante ne la réécrit pas (D47).
"""
from datetime import date, datetime

import streamlit as st

from dashboard.composants import (
    PROPORTIONS_LIGNE_PROSPECT,
    accorder,
    cellule_double,
    cellule_ou_absente,
    etat_vide,
    recapitulatif,
    titre_ecran,
)
from dashboard.lignes_demandes import afficher_entetes_demandes, afficher_lignes_demandes
from src.auth.types import UtilisateurContexte
from src.canaux.types import TenantContexte
from src.consultation.prospects import consulter_prospect, lister_prospects
from src.consultation.types import DetailProspect, LigneListeProspect
from src.db.session import ouvrir_session
from src.indicateurs.periodes import LIBELLES_PERIODES, periode_depuis_libelle
from src.presentation.montant import formater_nombre

# Le carnet s'ouvre sur tout ce que l'entreprise connaît, pas sur le mois en
# cours : on vient y chercher quelqu'un, pas un bilan de période (voir D48
# pour la période « Tout », et D49 pour ce choix de défaut).
PERIODE_PAR_DEFAUT = LIBELLES_PERIODES[3]

# Mêmes règles d'ellipse que les lignes de demandes, sur le préfixe de clé de
# cet écran. Le reste (fond, bordures, survol, bouton) vient des règles
# génériques [class*="st-key-ligne-"] de dashboard/style.py.
CSS_LIGNES_PROSPECT = """
<style>
[class*="st-key-ligne-prospect-"] {
    padding: 0.65rem 0.9rem !important;
}
[class*="st-key-ligne-prospect-"] div[data-testid="stColumn"] div[data-testid="stMarkdownContainer"] {
    overflow: hidden;
}
[class*="st-key-ligne-prospect-"] div[data-testid="stColumn"] div[data-testid="stMarkdownContainer"] div,
[class*="st-key-ligne-prospect-"] div[data-testid="stColumn"] div[data-testid="stMarkdownContainer"] span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
[class*="st-key-ligne-prospect-"] .stButton > button p {
    white-space: nowrap !important;
    word-break: keep-all !important;
    overflow: visible !important;
    text-overflow: unset !important;
}
/* Sans ce correctif, l'en-tête de la liste ne recevait que le style
   générique et discret de dashboard/style.py (fond gris, padding réduit) :
   les autres écrans le surmontent via ce même réglage, injecté ici pour que
   l'en-tête des prospects se lise comme celui des demandes plutôt que
   comme une variante plus pâle. */
[class*="st-key-entetes-"] {
    padding: 0.65rem 0.9rem !important;
    background: var(--surface) !important;
}
</style>
"""


def afficher_prospects(tenant: TenantContexte, utilisateur: UtilisateurContexte) -> None:
    """Liste des prospects du tenant, ou la fiche de celui qui est ouvert"""
    if "prospect_ouvert" in st.session_state:
        _afficher_fiche(tenant, st.session_state.prospect_ouvert)
        return
    _afficher_liste(tenant)


def _afficher_liste(tenant: TenantContexte) -> None:
    """Recherche et période, puis une ligne ouvrable par prospect"""
    st.markdown(
        titre_ecran(
            "Prospects",
            f"Les personnes qui ont demandé une estimation à {tenant.nom}.",
        ),
        unsafe_allow_html=True,
    )
    recherche, libelle_periode = _afficher_filtres()
    periode = periode_depuis_libelle(libelle_periode, date.today())

    with ouvrir_session() as session:
        prospects = lister_prospects(session, tenant.id, periode, recherche=recherche)

    if not prospects:
        st.markdown(
            _aucun_prospect(tenant, recherche, libelle_periode), unsafe_allow_html=True
        )
        return

    st.markdown(
        f'<div class="libelle-filtre">{accorder(len(prospects), "prospect")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(CSS_LIGNES_PROSPECT, unsafe_allow_html=True)
    _afficher_entetes_de_colonnes()
    for prospect in prospects:
        _afficher_ligne(prospect)


def _afficher_filtres() -> tuple[str, str]:
    """Champ de recherche et sélecteur de période, dont les valeurs sont renvoyées"""
    colonne_recherche, colonne_periode = st.columns([3, 2], vertical_alignment="bottom")
    with colonne_recherche:
        st.markdown('<div class="libelle-filtre">Rechercher</div>', unsafe_allow_html=True)
        # Conteneur porteur de la clé que la feuille de style cible : sans lui,
        # le champ se rend sans bordure et se lit comme un texte posé sur le
        # fond plutôt que comme un contrôle à côté des pilules de période.
        with st.container(key="recherche-prospects-boite"):
            recherche = st.text_input(
                "Rechercher",
                placeholder="Nom ou téléphone",
                key="recherche-prospects",
                label_visibility="collapsed",
            )
    with colonne_periode:
        st.markdown('<div class="libelle-filtre">Période</div>', unsafe_allow_html=True)
        with st.container(key="periode-prospects-boite"):
            periode = st.segmented_control(
                "Période",
                LIBELLES_PERIODES,
                default=PERIODE_PAR_DEFAUT,
                key="periode-prospects",
                label_visibility="collapsed",
            )
    return recherche or "", periode or PERIODE_PAR_DEFAUT


def _afficher_entetes_de_colonnes() -> None:
    """Les mêmes proportions que les lignes, pour que les colonnes s'alignent.

    Ni email ni relance ici : la relance concerne une demande, pas la
    personne (voir D49), et l'email reste un détail de coordonnées réservé à
    la fiche plutôt qu'une colonne de la liste.
    """
    entetes = (
        ("Prospect", ""),
        ("Demandes", " libelle-filtre--nb"),
        ("Dernière demande", ""),
        ("", ""),
    )
    with st.container(key="entetes-prospects"):
        colonnes = st.columns(PROPORTIONS_LIGNE_PROSPECT, vertical_alignment="center")
        for colonne, (entete, alignement) in zip(colonnes, entetes):
            colonne.markdown(
                f'<div class="libelle-filtre{alignement}">{entete}</div>',
                unsafe_allow_html=True,
            )


def _afficher_ligne(prospect: LigneListeProspect) -> None:
    """Un prospect par ligne, avec le bouton qui ouvre sa fiche.

    La clé du conteneur et celle du bouton dérivent de l'identifiant du
    prospect, jamais de son rang : une recherche réordonne la liste et
    recollerait sinon l'état d'un bouton sur la mauvaise ligne.
    """
    with st.container(key=f"ligne-prospect-{prospect.id}"):
        colonnes = st.columns(PROPORTIONS_LIGNE_PROSPECT, vertical_alignment="center")
        colonnes[0].markdown(
            cellule_double(prospect.nom, prospect.telephone), unsafe_allow_html=True
        )
        colonnes[1].markdown(
            f'<div class="table__nb table__principal">'
            f"{formater_nombre(prospect.nombre_demandes)}</div>",
            unsafe_allow_html=True,
        )
        colonnes[2].markdown(
            cellule_ou_absente(_jour(prospect.date_derniere_demande)),
            unsafe_allow_html=True,
        )
        if colonnes[3].button(
            "Ouvrir →", key=f"ouvrir-prospect-{prospect.id}", use_container_width=True
        ):
            st.session_state.prospect_ouvert = prospect.id
            st.rerun()


def _afficher_fiche(tenant: TenantContexte, prospect_id: str) -> None:
    """Coordonnées du prospect en haut, toutes ses demandes en dessous"""
    with ouvrir_session() as session:
        detail = consulter_prospect(session, tenant.id, prospect_id)

    if st.button("← Retour aux prospects", key="retour-prospects"):
        st.session_state.pop("prospect_ouvert", None)
        st.rerun()

    # Une fiche introuvable n'est pas une erreur à afficher crûment : elle
    # appartient à une autre entreprise, ou a été supprimée entre deux clics.
    if detail is None:
        st.markdown(
            etat_vide(
                "Prospect introuvable",
                "Cette fiche n'existe plus, ou n'appartient pas à votre entreprise.",
            ),
            unsafe_allow_html=True,
        )
        return

    resume = detail.resume
    st.markdown(
        titre_ecran(
            resume.nom,
            f"Prospect connu depuis le {_jour(resume.date_creation)}.",
        ),
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(_coordonnees(resume), unsafe_allow_html=True)
    _afficher_ses_demandes(detail)


def _coordonnees(prospect: LigneListeProspect) -> str:
    """De quoi rappeler la personne, la raison d'être de la table prospect (D26).

    Pas de relance ici : le consentement à être recontacté se donne à propos
    d'une demande précise, jamais de la personne dans l'absolu (voir D49) —
    il se lit sur le détail de chaque demande, pas sur cette fiche.
    """
    return recapitulatif(
        "Coordonnées",
        [
            ("Nom", prospect.nom),
            ("Téléphone", prospect.telephone),
            ("Email", prospect.email),
            ("Prospect depuis", _jour(prospect.date_creation)),
            ("Historique", accorder(prospect.nombre_demandes, "demande")),
        ],
    )


def _afficher_ses_demandes(detail: DetailProspect) -> None:
    """Son historique complet, dans la table même de l'écran des demandes.

    Aucune borne de période ici, contrairement à la liste : on regarde une
    personne, pas un mois.
    """
    st.write("")
    if not detail.demandes:
        st.markdown(
            etat_vide(
                "Aucune demande",
                "Ce prospect a laissé ses coordonnées sans qu'une demande n'aboutisse. "
                "Celles ci-dessus permettent de le rappeler.",
            ),
            unsafe_allow_html=True,
        )
        return

    # Le compte est déjà dans « Historique » juste au-dessus : le répéter ici
    # ferait lire deux fois le même chiffre à deux centimètres d'écart.
    st.markdown(
        '<div class="libelle-filtre">Demandes de ce prospect</div>', unsafe_allow_html=True
    )
    afficher_entetes_demandes("entetes-demandes-prospect")
    afficher_lignes_demandes(
        list(detail.demandes),
        prefixe_cle="ouvrir-demande-prospect",
        depuis_un_autre_ecran=True,
    )


def _jour(moment: datetime | None) -> str | None:
    """Date à la française, ou None pour que la cellule affiche son tiret"""
    return moment.strftime("%d/%m/%Y") if moment else None


def _aucun_prospect(
    tenant: TenantContexte, recherche: str, libelle_periode: str
) -> str:
    """État vide qui distingue « rien trouvé » de « rien reçu »"""
    if recherche:
        return etat_vide(
            "Aucun prospect ne correspond",
            f"Rien ne correspond à « {recherche} » sur la période choisie. "
            "Essayez un fragment du nom, ou les premiers chiffres du numéro.",
        )
    if libelle_periode != PERIODE_PAR_DEFAUT:
        return etat_vide(
            "Aucun prospect sur cette période",
            f"Aucune personne ne s'est présentée « {libelle_periode.lower()} ». "
            f"Choisissez « {PERIODE_PAR_DEFAUT} » pour voir tout votre carnet.",
        )
    return etat_vide(
        "Aucun prospect pour l'instant",
        "Les prospects arrivent par le lien d'estimation que vous partagez sur "
        "votre site ou vos réseaux. Voici celui de votre espace :",
        code=f"?slug={tenant.slug}",
    )
