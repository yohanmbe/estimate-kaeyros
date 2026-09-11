"""Écran des indicateurs (voir D19 et D48).

Aucun chiffre n'est calculé ici : chaque valeur sort d'une fonction de
src/indicateurs, testée séparément, qui filtre sur le tenant de la session.
L'écran ne fait que demander, mettre en forme et afficher.

Deux rangées : les cinq indicateurs sur une seule ligne, montant cumulé en
tête, puis le graphique par tranche d'invités seul en pleine largeur en
dessous (voir D48).
"""
from datetime import date

import streamlit as st

from dashboard.composants import (
    accorder,
    carte_indicateur,
    carte_montant,
    carte_tranches,
    etat_vide,
    titre_ecran,
)
from dashboard.lignes_demandes import afficher_entetes_demandes, afficher_lignes_demandes
from src.auth.types import UtilisateurContexte
from src.canaux.types import TenantContexte
from src.consultation.demandes import lister_demandes
from src.consultation.types import LigneListeDemande
from src.db.session import ouvrir_session
from src.indicateurs.chiffrage import calculer_taux_demandes_chiffrees
from src.indicateurs.demandes import compter_demandes, repartir_par_tranche_invites
from src.indicateurs.devis import calculer_montant_total
from src.indicateurs.periodes import LIBELLES_PERIODES, periode_depuis_libelle
from src.indicateurs.prospects import calculer_taux_consentement_contact, compter_prospects
from src.indicateurs.types import Periode
from src.presentation.montant import formater_nombre

NOMBRE_DERNIERES_DEMANDES = 5


def afficher_tableau_de_bord(
    tenant: TenantContexte, utilisateur: UtilisateurContexte
) -> None:
    """Indicateurs de la période choisie, puis les dernières demandes reçues"""
    libelle_periode = _afficher_entete(tenant)
    periode = periode_depuis_libelle(libelle_periode, date.today())

    with ouvrir_session() as session:
        nombre_demandes = compter_demandes(session, tenant.id, periode)
        montant_total = calculer_montant_total(session, tenant.id, periode)
        tranches = repartir_par_tranche_invites(session, tenant.id, periode)
        nombre_prospects = compter_prospects(session, tenant.id, periode)
        taux_consentement = calculer_taux_consentement_contact(session, tenant.id, periode)
        taux_chiffrees = calculer_taux_demandes_chiffrees(session, tenant.id, periode)
        dernieres = lister_demandes(
            session, tenant.id, periode, limite=NOMBRE_DERNIERES_DEMANDES
        )

    _afficher_cartes(
        nombre_demandes, nombre_prospects, montant_total,
        taux_consentement, taux_chiffrees, libelle_periode,
    )
    _afficher_graphique_tranches(tranches, libelle_periode)
    _afficher_dernieres_demandes(dernieres, tenant, periode)


def _afficher_entete(tenant: TenantContexte) -> str:
    """Titre de l'écran et sélecteur de période, dont il renvoie le libellé choisi"""
    colonne_titre, colonne_periode = st.columns([3, 2], vertical_alignment="center")
    colonne_titre.markdown(
        titre_ecran("Tableau de bord", f"Activité de pré-cotation de {tenant.nom}."),
        unsafe_allow_html=True,
    )
    with colonne_periode:
        choix = st.segmented_control(
            "Période",
            LIBELLES_PERIODES,
            default=LIBELLES_PERIODES[0],
            key="periode-tableau-de-bord",
            label_visibility="collapsed",
        )
    # Le sélecteur renvoie None si le gestionnaire déselectionne son choix :
    # l'écran retombe alors sur la première période plutôt que de planter.
    return choix or LIBELLES_PERIODES[0]


def _afficher_cartes(
    nombre_demandes: int,
    nombre_prospects: int,
    montant_total: int,
    taux_consentement: int,
    taux_chiffrees: int,
    libelle_periode: str,
) -> None:
    """Les cinq indicateurs sur une seule ligne, le montant cumulé en tête :
    c'est le chiffre que le gestionnaire regarde en premier, dans une carte à
    sa propre taille (la coquille par défaut, plus grande) pendant que les
    quatre autres partagent une taille plus dense mais identique entre elles.
    """
    st.write("")
    cartes = st.columns([1.6, 1, 1, 1, 1], gap="medium")
    cartes[0].markdown(
        carte_montant("Total estimé cumulé", montant_total, "somme des estimations émises"),
        unsafe_allow_html=True,
    )
    cartes[1].markdown(
        carte_indicateur(
            "Demandes reçues", formater_nombre(nombre_demandes), libelle_periode.lower(),
            modificateur="compact",
        ),
        unsafe_allow_html=True,
    )
    cartes[2].markdown(
        carte_indicateur(
            "Nombre de prospects", formater_nombre(nombre_prospects), libelle_periode.lower(),
            modificateur="compact",
        ),
        unsafe_allow_html=True,
    )
    cartes[3].markdown(
        carte_indicateur(
            "Relance autorisée", str(taux_consentement), "des prospects",
            unite="%", modificateur="compact",
        ),
        unsafe_allow_html=True,
    )
    cartes[4].markdown(
        carte_indicateur(
            "Estimations envoyées", str(taux_chiffrees), "des demandes",
            unite="%", modificateur="compact",
        ),
        unsafe_allow_html=True,
    )


def _afficher_graphique_tranches(tranches: list, libelle_periode: str) -> None:
    """Le graphique par tranche d'invités, seul en pleine largeur.

    Une carte à lui seul plutôt qu'un tiers de rangée : à hauteur de carte
    numérique, l'écart entre deux tranches ne se voyait plus à l'œil, alors
    que le calcul est déjà proportionnel (voir carte_tranches).
    """
    st.write("")
    st.markdown(
        carte_tranches(
            "Demandes par tranche d'invités", tranches, libelle_periode.lower(), grande=True
        ),
        unsafe_allow_html=True,
    )


def _afficher_dernieres_demandes(
    dernieres: list[LigneListeDemande], tenant: TenantContexte, periode: Periode
) -> None:
    """Les cinq dernières demandes, chacune ouvrable, avec un passage vers la liste complète"""
    st.write("")
    colonne_titre, colonne_lien = st.columns([3, 1], vertical_alignment="center")
    colonne_titre.markdown(
        '<div class="libelle-filtre">Dernières demandes reçues</div>', unsafe_allow_html=True
    )
    with colonne_lien:
        if st.button("Voir la liste complète →", key="voir-toutes-les-demandes"):
            st.session_state.ecran = "demandes"
            st.rerun()

    if not dernieres:
        st.markdown(_aucune_demande(tenant), unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="libelle-filtre">{accorder(len(dernieres), "demande")}</div>',
        unsafe_allow_html=True,
    )
    afficher_entetes_demandes("entetes-dernieres-demandes")
    afficher_lignes_demandes(
        dernieres, prefixe_cle="ouvrir-derniere", depuis_un_autre_ecran=True
    )


def _aucune_demande(tenant: TenantContexte) -> str:
    """État vide expliqué : par où arrivent les demandes, et avec quel lien"""
    return etat_vide(
        "Aucune demande sur cette période",
        "Les demandes arrivent par le lien d'estimation que vous partagez sur votre "
        "site ou vos réseaux. Essayez une autre période, ou vérifiez que le lien "
        "ci-dessous est bien celui que vos prospects utilisent.",
        code=f"?slug={tenant.slug}",
    )
