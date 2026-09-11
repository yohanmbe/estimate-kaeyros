"""Écran des indicateurs (voir D19).

Aucun chiffre n'est calculé ici : chaque valeur sort d'une fonction de
src/indicateurs, testée séparément, qui filtre sur le tenant de la session.
L'écran ne fait que demander, mettre en forme et afficher.

Quatre cartes pour les quatre indicateurs de D19, puis une bande discrète pour
les trois indicateurs complémentaires : les faire toutes peser pareil ne
hiérarchiserait rien à l'œil.
"""
from datetime import date

import streamlit as st

from dashboard.composants import (
    CSS_LIGNES_DEMANDE,
    PROPORTIONS_LIGNE_DEMANDE,
    accorder,
    bande_indicateur,
    carte_indicateur,
    carte_montant,
    carte_tranches,
    cellule_double,
    cellule_montant,
    cellule_ou_absente,
    date_francaise,
    etat_vide,
    pastille_etat,
    resume_evenement,
    titre_ecran,
)
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

    _afficher_cartes(nombre_demandes, montant_total, tranches, libelle_periode)
    _afficher_indicateurs_complementaires(nombre_prospects, taux_consentement, taux_chiffrees)
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
    nombre_demandes: int, montant_total: int, tranches: list, libelle_periode: str
) -> None:
    """Trois des quatre indicateurs de D19, sur une seule ligne.

    Le montant moyen reste calculable (voir src/indicateurs/devis.py) mais
    n'est plus affiché ici, à la demande du gestionnaire : voir D19.
    """
    st.write("")
    cartes = st.columns(3, gap="medium")
    cartes[0].markdown(
        carte_indicateur(
            "Demandes reçues", formater_nombre(nombre_demandes), libelle_periode.lower()
        ),
        unsafe_allow_html=True,
    )
    cartes[1].markdown(
        carte_montant("Total estimé cumulé", montant_total, "somme des estimations émises"),
        unsafe_allow_html=True,
    )
    cartes[2].markdown(
        carte_tranches("Par nombre d'invités", tranches, "demandes par tranche"),
        unsafe_allow_html=True,
    )


def _afficher_indicateurs_complementaires(
    nombre_prospects: int, taux_consentement: int, taux_chiffrees: int
) -> None:
    """Trois repères qui complètent D19 sans mesurer aucune conversion commerciale"""
    st.write("")
    bandes = st.columns(3, gap="medium")
    bandes[0].markdown(
        bande_indicateur(formater_nombre(nombre_prospects), "prospects identifiés sur la période"),
        unsafe_allow_html=True,
    )
    bandes[1].markdown(
        bande_indicateur(f"{taux_consentement} %", "des prospects acceptent d'être recontactés"),
        unsafe_allow_html=True,
    )
    bandes[2].markdown(
        bande_indicateur(f"{taux_chiffrees} %", "des demandes ont reçu une estimation"),
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
    st.markdown(CSS_LIGNES_DEMANDE, unsafe_allow_html=True)
    _afficher_entetes_dernieres()
    for demande in dernieres:
        _afficher_ligne_derniere(demande)


def _afficher_entetes_dernieres() -> None:
    """Mêmes en-têtes, mêmes proportions et même style que dashboard/demandes.py :
    cet aperçu doit se lire comme la même table, pas comme une variante.
    """
    entetes = (
        ("Reçue le", ""),
        ("Événement", ""),
        ("Date prévue", ""),
        ("Total estimé", " libelle-filtre--nb"),
        ("Statut", ""),
        ("", ""),
    )
    with st.container(key="entetes-dernieres-demandes"):
        colonnes = st.columns(PROPORTIONS_LIGNE_DEMANDE, vertical_alignment="center")
        for colonne, (entete, alignement) in zip(colonnes, entetes):
            colonne.markdown(
                f'<div class="libelle-filtre{alignement}">{entete}</div>',
                unsafe_allow_html=True,
            )


def _afficher_ligne_derniere(demande: LigneListeDemande) -> None:
    """Une demande par ligne, ouvrable comme depuis l'écran des demandes.

    La clé du conteneur commence par « ligne-demande- », comme dans
    dashboard/demandes.py : c'est ce préfixe que CSS_LIGNES_DEMANDE cible pour
    tronquer proprement un texte trop long plutôt que de le laisser déborder
    de sa boîte. Elle dérive de l'identifiant de la demande, jamais de son
    rang, un changement de période réordonnant la liste.
    """
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
            "Ouvrir →", key=f"ouvrir-derniere-{demande.id}", use_container_width=True
        ):
            st.session_state.ecran = "demandes"
            st.session_state.demande_ouverte = demande.id
            st.rerun()


def _aucune_demande(tenant: TenantContexte) -> str:
    """État vide expliqué : par où arrivent les demandes, et avec quel lien"""
    return etat_vide(
        "Aucune demande sur cette période",
        "Les demandes arrivent par le lien d'estimation que vous partagez sur votre "
        "site ou vos réseaux. Essayez une autre période, ou vérifiez que le lien "
        "ci-dessous est bien celui que vos prospects utilisent.",
        code=f"?slug={tenant.slug}",
    )
