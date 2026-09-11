"""La table des demandes reçues, partagée par les écrans qui la montrent.

Trois écrans l'affichent : la liste complète (dashboard/demandes.py), l'aperçu
des dernières reçues (dashboard/tableau_de_bord.py) et la fiche d'un prospect
(dashboard/prospects.py). Elle vit ici plutôt que recopiée trois fois, pour
que les trois se lisent comme la même table et non comme trois tables qui se
ressemblent à peu près (voir D49).

Ce module appelle Streamlit, contrairement à dashboard/composants.py qui reste
purement du HTML : c'est justement ce qui l'en sépare. Les cellules, elles,
continuent de sortir de composants.py.
"""
import streamlit as st

from dashboard.composants import (
    CSS_LIGNES_DEMANDE,
    PROPORTIONS_LIGNE_DEMANDE,
    cellule_double,
    cellule_montant,
    cellule_ou_absente,
    date_francaise,
    pastille_etat,
    resume_evenement,
)
from src.consultation.types import LigneListeDemande

ENTETES = (
    ("Reçue le", ""),
    ("Événement", ""),
    ("Date prévue", ""),
    ("Total estimé", " libelle-filtre--nb"),
    ("Statut", ""),
    ("", ""),
)


def afficher_entetes_demandes(cle_conteneur: str) -> None:
    """Les six en-têtes, aux proportions exactes des lignes qui suivent.

    La clé du conteneur est propre à l'écran appelant : elle commence par
    « entetes- », le préfixe que la feuille de style cible pour les distinguer
    des lignes (qui, elles, se tronquent à l'ellipse).
    """
    with st.container(key=cle_conteneur):
        colonnes = st.columns(PROPORTIONS_LIGNE_DEMANDE, vertical_alignment="center")
        for colonne, (entete, alignement) in zip(colonnes, ENTETES):
            colonne.markdown(
                f'<div class="libelle-filtre{alignement}">{entete}</div>',
                unsafe_allow_html=True,
            )


def afficher_lignes_demandes(
    demandes: list[LigneListeDemande],
    prefixe_cle: str,
    depuis_un_autre_ecran: bool = False,
) -> None:
    """Une demande par ligne, chacune ouvrable sur son détail.

    prefixe_cle distingue les boutons d'un écran à l'autre. Il ne dérive
    jamais du rang de la ligne, seulement de l'identifiant de la demande : un
    changement de filtre réordonne la liste et recollerait sinon l'état d'un
    bouton sur la mauvaise ligne.

    depuis_un_autre_ecran vaut vrai partout sauf sur l'écran des demandes :
    le clic doit alors aussi changer d'écran, et oublier la fiche prospect
    éventuellement ouverte pour que la navigation reste un trajet et non une
    pile où l'on revient sans l'avoir demandé.
    """
    st.markdown(CSS_LIGNES_DEMANDE, unsafe_allow_html=True)
    for demande in demandes:
        _afficher_ligne(demande, prefixe_cle, depuis_un_autre_ecran)


def _afficher_ligne(
    demande: LigneListeDemande, prefixe_cle: str, depuis_un_autre_ecran: bool
) -> None:
    """Les six cellules d'une demande, puis son bouton d'ouverture"""
    with st.container(key=f"ligne-demande-{demande.id}"):
        colonnes = st.columns(PROPORTIONS_LIGNE_DEMANDE, vertical_alignment="center")
        colonnes[0].markdown(
            cellule_double(
                demande.date_creation.strftime("%d/%m/%Y"),
                demande.prospect.nom if demande.prospect else "Prospect inconnu",
            ),
            unsafe_allow_html=True,
        )
        colonnes[1].markdown(
            cellule_double(
                (demande.type_evenement or "Événement").capitalize(),
                resume_evenement(demande) or None,
            ),
            unsafe_allow_html=True,
        )
        colonnes[2].markdown(
            cellule_ou_absente(date_francaise(demande.date_evenement)),
            unsafe_allow_html=True,
        )
        colonnes[3].markdown(
            f'<div class="table__nb table__principal">'
            f"{cellule_montant(demande.total_dernier_devis, demande.devise)}</div>",
            unsafe_allow_html=True,
        )
        colonnes[4].markdown(pastille_etat(demande.etat), unsafe_allow_html=True)
        if colonnes[5].button(
            "Ouvrir →", key=f"{prefixe_cle}-{demande.id}", use_container_width=True
        ):
            _ouvrir(demande.id, depuis_un_autre_ecran)


def _ouvrir(demande_id: str, depuis_un_autre_ecran: bool) -> None:
    """Pose la demande à ouvrir en session, et l'écran qui sait l'afficher"""
    st.session_state.demande_ouverte = demande_id
    if depuis_un_autre_ecran:
        st.session_state.ecran = "demandes"
        st.session_state.pop("prospect_ouvert", None)
    st.rerun()
