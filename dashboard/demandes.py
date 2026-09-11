"""Écran des demandes reçues, en lecture seule.

Le gestionnaire consulte, il ne modifie rien : une demande est ce que le
prospect a décrit, un devis émis est un document figé (D11). Les montants
affichés sont relus en base, jamais recalculés.

Le détail s'ouvre dans la page, sous la liste, et non dans une fenêtre modale :
un devis complet se lit mal dans une modale, et un panneau intégré reste
pilotable par les tests d'écran.
"""
from datetime import date
from html import escape

import streamlit as st

from dashboard.composants import (
    LIBELLES_ETATS,
    accorder,
    date_francaise,
    etat_vide,
    panneau,
    pastille_categorie,
    pastille_etat,
    recapitulatif,
    tableau_devis,
    titre_ecran,
)
from dashboard.lignes_demandes import afficher_entetes_demandes, afficher_lignes_demandes
from src.auth.types import UtilisateurContexte
from src.canaux.types import TenantContexte
from src.consultation.demandes import consulter_demande, lister_demandes
from src.consultation.types import DetailDemande, ProspectDeLaDemande
from src.db.models import ETAT_COMPLETE, ETAT_EN_COURS
from src.db.session import ouvrir_session
from src.indicateurs.periodes import LIBELLES_PERIODES, periode_depuis_libelle
from src.presentation.montant import formater_nombre

FILTRE_TOUS = "Tous"

# « Abandonnée » n'est pas proposé : rien dans le produit ne sait déclarer
# qu'une conversation est abandonnée plutôt qu'en pause (voir DONNEES.md), et
# un filtre qui ne peut jamais rien renvoyer vaut moins que pas de filtre.
ETATS_FILTRABLES: dict[str, str | None] = {
    FILTRE_TOUS: None,
    LIBELLES_ETATS[ETAT_EN_COURS]: ETAT_EN_COURS,
    LIBELLES_ETATS[ETAT_COMPLETE]: ETAT_COMPLETE,
}

# Le canal est stocké en clair dans la base (voir DONNEES.md) ; le gestionnaire
# lit le nom du service, pas celui de la bibliothèque qui le rend.
LIBELLES_CANAUX: dict[str, str] = {"streamlit": "le chat en ligne", "whatsapp": "WhatsApp"}


def libelle_canal(canal: str) -> str:
    """Nom affichable du canal par lequel la demande est arrivée"""
    return LIBELLES_CANAUX.get(canal, canal)


def afficher_demandes(tenant: TenantContexte, utilisateur: UtilisateurContexte) -> None:
    """Liste des demandes du tenant, ou le détail de celle qui est ouverte"""
    if "demande_ouverte" in st.session_state:
        _afficher_detail(tenant, st.session_state.demande_ouverte)
        return
    _afficher_liste(tenant)


def _afficher_liste(tenant: TenantContexte) -> None:
    """Filtres, puis une ligne cliquable par demande"""
    st.markdown(
        titre_ecran(
            "Demandes reçues", f"Demandes adressées à {tenant.nom} via le chat Estimate."
        ),
        unsafe_allow_html=True,
    )
    libelle_etat, libelle_periode = _afficher_filtres()
    periode = periode_depuis_libelle(libelle_periode, date.today())

    with ouvrir_session() as session:
        demandes = lister_demandes(
            session, tenant.id, periode, etat=ETATS_FILTRABLES[libelle_etat]
        )

    if not demandes:
        st.markdown(_aucune_demande(tenant, libelle_etat), unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="libelle-filtre">{accorder(len(demandes), "demande")}</div>',
        unsafe_allow_html=True,
    )
    afficher_entetes_demandes("entetes-demandes")
    afficher_lignes_demandes(demandes, prefixe_cle="ouvrir")


def _afficher_filtres() -> tuple[str, str]:
    """Sélecteurs de statut et de période, dont les libellés choisis sont renvoyés"""
    colonne_etat, colonne_periode = st.columns([3, 2], vertical_alignment="bottom")
    with colonne_etat:
        st.markdown('<div class="libelle-filtre">Statut</div>', unsafe_allow_html=True)
        etat = st.segmented_control(
            "Statut",
            list(ETATS_FILTRABLES),
            default=FILTRE_TOUS,
            key="statut-demandes",
            label_visibility="collapsed",
        )
    with colonne_periode:
        st.markdown('<div class="libelle-filtre">Période</div>', unsafe_allow_html=True)
        periode = st.segmented_control(
            "Période",
            LIBELLES_PERIODES,
            default=LIBELLES_PERIODES[2],
            key="periode-demandes",
            label_visibility="collapsed",
        )
    return etat or FILTRE_TOUS, periode or LIBELLES_PERIODES[2]


def _afficher_detail(tenant: TenantContexte, demande_id: str) -> None:
    """Besoin décrit, coordonnées du prospect et devis émis pour cette demande"""
    with ouvrir_session() as session:
        detail = consulter_demande(session, tenant.id, demande_id)

    if st.button("← Retour aux demandes", key="retour-demandes"):
        st.session_state.pop("demande_ouverte", None)
        st.rerun()

    # Une demande introuvable n'est pas une erreur à afficher crûment : elle
    # appartient à une autre entreprise, ou a été supprimée entre deux clics.
    if detail is None:
        st.markdown(
            etat_vide(
                "Demande introuvable",
                "Cette demande n'existe plus, ou n'appartient pas à votre entreprise.",
            ),
            unsafe_allow_html=True,
        )
        return

    resume = detail.resume
    nom_prospect = resume.prospect.nom if resume.prospect else "Prospect inconnu"
    st.markdown(
        titre_ecran(
            nom_prospect,
            f"Demande reçue le {resume.date_creation.strftime('%d/%m/%Y à %H:%M')} "
            f"via {libelle_canal(resume.canal)}.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(pastille_etat(resume.etat), unsafe_allow_html=True)
    st.write("")

    colonne_besoin, colonne_prospect = st.columns(2, gap="medium")
    colonne_besoin.markdown(_recapitulatif_besoin(detail), unsafe_allow_html=True)
    with colonne_prospect:
        st.markdown(_recapitulatif_prospect(detail), unsafe_allow_html=True)
        _afficher_lien_vers_la_fiche(resume.prospect)

    _afficher_mots_du_prospect(detail)
    _afficher_demandes_sur_mesure(detail)
    _afficher_devis(detail)


def _afficher_lien_vers_la_fiche(prospect: ProspectDeLaDemande | None) -> None:
    """Passage vers la fiche du prospect, quand la demande en a un.

    Le bouton est posé à côté du récapitulatif plutôt que dedans :
    _recapitulatif_prospect reste une fonction pure qui ne fait que du HTML.
    """
    if prospect is None:
        return
    if st.button("Voir la fiche prospect →", key="voir-fiche-prospect"):
        st.session_state.ecran = "prospects"
        st.session_state.prospect_ouvert = prospect.id
        st.session_state.pop("demande_ouverte", None)
        st.rerun()


def _afficher_demandes_sur_mesure(detail: DetailDemande) -> None:
    """Les prestations que le prospect attend de vous, faute d'avoir trouvé au catalogue.

    C'est une intention d'achat que le catalogue n'a pas su servir : elle
    n'apparaît sur aucun devis, et se perdrait si l'écran ne la montrait pas.
    """
    categories = (detail.besoin or {}).get("categories_sur_mesure") or []
    if not categories:
        return
    st.write("")
    st.markdown(
        panneau(
            "Proposition sur mesure attendue",
            accorder(len(categories), "prestation", "prestations"),
            '<div class="texte-libre">'
            + "".join(pastille_categorie(categorie) for categorie in categories)
            + "</div>",
        ),
        unsafe_allow_html=True,
    )


def _afficher_mots_du_prospect(detail: DetailDemande) -> None:
    """Ce que le prospect a écrit en clair, hors de tout ce que le LLM a extrait.

    C'est la partie que le commercial lit en premier pour rappeler quelqu'un :
    elle dit ce que le catalogue n'a pas su couvrir, dans les mots du prospect.
    """
    sections = [
        ("Besoins hors catalogue", detail.besoins_hors_catalogue),
        ("Mot du prospect", detail.commentaire),
    ]
    for titre, texte in sections:
        if not texte:
            continue
        st.write("")
        st.markdown(
            panneau(titre, "", f'<div class="texte-libre">{escape(texte)}</div>'),
            unsafe_allow_html=True,
        )


def _recapitulatif_besoin(detail: DetailDemande) -> str:
    """L'événement tel que le prospect l'a décrit, champs manquants compris"""
    resume = detail.resume
    besoin = detail.besoin or {}
    duree = besoin.get("duree_jours")
    budget = besoin.get("budget_declare")
    return recapitulatif(
        "L'événement",
        [
            ("Type", (resume.type_evenement or "").capitalize() or None),
            ("Date", date_francaise(resume.date_evenement)),
            ("Ville", resume.ville),
            ("Quartier souhaité", resume.quartier_souhaite),
            (
                "Invités",
                formater_nombre(resume.nombre_invites) if resume.nombre_invites else None,
            ),
            ("Durée", f"{duree} jour(s)" if duree else None),
            ("Budget déclaré", formater_nombre(budget) if budget else None),
        ],
    )


def _recapitulatif_prospect(detail: DetailDemande) -> str:
    """Coordonnées de rappel, la raison d'être de la table prospect (D26)"""
    prospect = detail.resume.prospect
    if prospect is None:
        return recapitulatif("Demandé par", [("Coordonnées", None)])
    return recapitulatif(
        "Demandé par",
        [
            ("Nom", prospect.nom),
            ("Téléphone", prospect.telephone),
            ("Email", prospect.email),
            (
                "Relance autorisée",
                "Oui" if prospect.consentement_contact else "Non",
            ),
            ("Historique", _historique_prospect(prospect.nombre_demandes)),
        ],
    )


def _historique_prospect(nombre_demandes: int) -> str:
    """Rappelle qu'un prospect reconnu (même téléphone, voir D47) est déjà revenu"""
    if nombre_demandes <= 1:
        return "Première demande"
    return f"{accorder(nombre_demandes, 'demande')} au total"


def _afficher_devis(detail: DetailDemande) -> None:
    """Les devis émis, du plus récent au plus ancien, tels qu'ils ont été figés"""
    st.write("")
    if not detail.devis:
        st.markdown(
            etat_vide(
                "Aucune estimation émise",
                "La conversation s'est arrêtée avant le chiffrage. Les coordonnées "
                "ci-dessus permettent de rappeler ce prospect.",
            ),
            unsafe_allow_html=True,
        )
        return

    for rang, devis in enumerate(detail.devis):
        libelle = "Estimation envoyée le" if rang == 0 else "Estimation précédente du"
        st.markdown(
            f'<div class="libelle-filtre">{libelle} '
            f'{devis.date_emission.strftime("%d/%m/%Y à %H:%M")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(tableau_devis(devis), unsafe_allow_html=True)
        st.write("")


def _aucune_demande(tenant: TenantContexte, libelle_etat: str) -> str:
    """État vide qui distingue « rien reçu » de « rien dans ce filtre »"""
    if libelle_etat != FILTRE_TOUS:
        return etat_vide(
            "Aucune demande avec ce statut",
            f"Aucune demande « {libelle_etat.lower()} » sur la période choisie. "
            "Changez de statut ou de période pour voir les autres.",
        )
    return etat_vide(
        "Aucune demande sur cette période",
        "Les demandes arrivent par le lien d'estimation que vous partagez sur votre "
        "site ou vos réseaux. Voici celui de votre espace :",
        code=f"?slug={tenant.slug}",
    )
