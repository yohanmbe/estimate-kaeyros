"""Écran du catalogue : lecture et écriture des prestations du tenant.

Ces prix sont la source unique des montants de toutes les estimations (D01) :
ce qui s'écrit ici finit dans un devis. La validation vit dans
src/catalogue/edition.py, l'écran ne fait que présenter ses refus.

Le formulaire adapte ses champs à la catégorie choisie, en bouclant sur
SCHEMA_ATTRIBUTS (voir src/catalogue/vocabulaire.py) plutôt qu'avec une suite
de cas particuliers. La catégorie se choisit hors du formulaire : dans un
st.form, changer une liste déroulante ne déclenche aucun réaffichage, et les
champs de la nouvelle catégorie n'apparaîtraient qu'après validation.
"""
from html import escape

import streamlit as st

from dashboard.composants import (
    accorder,
    cellule_double,
    etat_vide,
    pastille_categorie,
    titre_ecran,
)
from src.auth.types import UtilisateurContexte
from src.canaux.types import TenantContexte
from src.catalogue.edition import (
    RessourceGestion,
    SaisieRessource,
    basculer_activation,
    creer_ressource,
    lister_pour_gestion,
    modifier_ressource,
    supprimer_ressource,
    valider_saisie,
)
from src.catalogue.vocabulaire import (
    CATEGORIES,
    UNITE_HABITUELLE,
    UNITES_FACTURATION,
    ChampAttribut,
    champs_attributs,
    libelle_categorie,
    libelle_unite,
)
from src.db.session import ouvrir_session
from src.presentation.montant import formater_montant

FILTRE_TOUTES = "Toutes"
NOUVELLE_PRESTATION = "nouvelle"

PREFIXE_SAISIE = "edition-"
# Dernière catégorie rendue, pour détecter un changement et réinitialiser les
# champs qui en dépendent (voir _suivre_la_categorie).
CLE_CATEGORIE_VUE = f"{PREFIXE_SAISIE}categorie-vue"

NIVEAU_SUCCES = "succes"
NIVEAU_ALERTE = "alerte"
# Prestation, catégorie, unité, prix, puis deux actions : le statut ne figure
# plus en colonne, chacune des deux sections (actives / retirées) le dit déjà
# par son titre.
PROPORTIONS_COLONNES = (2.8, 1.2, 1.2, 1.5, 1.1, 1.3)
CLE_CONFIRMATION_SUPPRESSION = "confirmation-suppression"

PRIX_MAXIMUM = 100_000_000
PAS_DE_PRIX = 5_000

CSS_TABLEAU = """
<style>
[class*="st-key-ligne-prestation-"] {
    padding: 0.65rem 0.9rem !important;
}

[class*="st-key-entetes-catalogue-"] {
    padding: 0.65rem 0.9rem !important;
    background: var(--surface) !important;
}

[class*="st-key-ligne-prestation-"] .stButton > button p {
    white-space: nowrap !important;
    word-break: keep-all !important;
}
</style>
"""

def afficher_catalogue(tenant: TenantContexte, utilisateur: UtilisateurContexte) -> None:
    """Liste des prestations du tenant, ou le formulaire d'ajout et de modification"""
    if "ressource_en_edition" in st.session_state:
        _afficher_formulaire(tenant, st.session_state.ressource_en_edition)
        return
    _afficher_liste(tenant)


def _afficher_liste(tenant: TenantContexte) -> None:
    """Filtre par catégorie, puis une ligne par prestation"""
    colonne_titre, colonne_ajout = st.columns([3, 1], vertical_alignment="center")
    colonne_titre.markdown(
        titre_ecran(
            "Catalogue des prestations",
            "Ces prix composent toutes les estimations envoyées aux prospects.",
        ),
        unsafe_allow_html=True,
    )
    with colonne_ajout:
        if st.button(
            "＋ Ajouter une prestation", key="ajouter-prestation", type="primary",
            use_container_width=True,
        ):
            _ouvrir_formulaire(NOUVELLE_PRESTATION)

    _afficher_message()

    categorie = _afficher_filtre_categories()
    with ouvrir_session() as session:
        prestations = lister_pour_gestion(
            session, tenant.id, categorie=None if categorie == FILTRE_TOUTES else categorie
        )

    if not prestations:
        st.markdown(_aucune_prestation(categorie), unsafe_allow_html=True)
        return

    actives = [prestation for prestation in prestations if prestation.actif]
    retirees = [prestation for prestation in prestations if not prestation.actif]

    if actives:
        st.markdown(
            f'<div class="libelle-filtre">{accorder(len(actives), "prestation")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(CSS_TABLEAU, unsafe_allow_html=True)
        _afficher_entetes_de_colonnes()
        for prestation in actives:
            _afficher_ligne(tenant, prestation)
    else:
        st.markdown(
            etat_vide(
                "Aucune prestation active dans cette catégorie",
                "Les prestations retirées de cette catégorie sont plus bas, "
                "si vous voulez en remettre une en service.",
            ),
            unsafe_allow_html=True,
        )

    if retirees:
        _afficher_bloc_retirees(tenant, retirees)


def _afficher_bloc_retirees(tenant: TenantContexte, retirees: list[RessourceGestion]) -> None:
    """Bloc distinct, sous la liste active : remettre en service ou supprimer.

    Volontairement éloigné et visuellement en retrait de la liste active, pour
    qu'une prestation retirée ne se confonde jamais avec celles que le
    prospect peut encore se voir proposer.
    """
    st.markdown('<div class="separateur-retirees"></div>', unsafe_allow_html=True)
    st.markdown(
        titre_ecran(
            "Prestations retirées",
            "Elles ne sont plus proposées aux prospects. Remettez-les en service, "
            "ou supprimez-les définitivement si vous ne vous en servirez plus.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="libelle-filtre">{accorder(len(retirees), "prestation retirée", "prestations retirées")}</div>',
        unsafe_allow_html=True,
    )
    _afficher_entetes_de_colonnes(retirees=True)
    for prestation in retirees:
        _afficher_ligne(tenant, prestation)


def _afficher_filtre_categories() -> str:
    """Sélecteur de catégorie, en pilules plutôt qu'en onglets.

    st.tabs afficherait le contenu de tous les onglets à chaque exécution,
    soit une requête par catégorie pour une seule liste visible.
    """
    st.markdown('<div class="libelle-filtre">Catégorie</div>', unsafe_allow_html=True)
    choix = st.segmented_control(
        "Catégorie",
        [FILTRE_TOUTES, *CATEGORIES],
        default=FILTRE_TOUTES,
        format_func=lambda valeur: (
            FILTRE_TOUTES if valeur == FILTRE_TOUTES else libelle_categorie(valeur).capitalize()
        ),
        key="categorie-catalogue",
        label_visibility="collapsed",
    )
    return choix or FILTRE_TOUTES


def _afficher_entetes_de_colonnes(retirees: bool = False) -> None:
    """Mêmes proportions que les lignes, pour que les colonnes s'alignent"""
    entetes = (
        ("Prestation", ""),
        ("Catégorie", ""),
        ("Unité", ""),
        ("Prix unitaire", " libelle-filtre--nb"),
        ("", ""),
        ("", ""),
    )
    with st.container(key=f"entetes-catalogue-{'retirees' if retirees else 'actives'}"):
        colonnes = st.columns(PROPORTIONS_COLONNES, vertical_alignment="center")
        for colonne, (entete, alignement) in zip(colonnes, entetes):
            colonne.markdown(
                f'<div class="libelle-filtre{alignement}">{entete}</div>',
                unsafe_allow_html=True,
            )


def _afficher_ligne(tenant: TenantContexte, prestation: RessourceGestion) -> None:
    """Une prestation par ligne, avec ses deux actions.

    Les clés dérivent de l'identifiant de la prestation et jamais de son rang :
    un changement de filtre réordonne la liste et recollerait sinon un clic sur
    la mauvaise ligne.
    """
    en_confirmation = st.session_state.get(CLE_CONFIRMATION_SUPPRESSION) == prestation.id
    prefixe_cle = "ligne-prestation" if prestation.actif else "ligne-prestation-retiree"
    with st.container(key=f"{prefixe_cle}-{prestation.id}"):
        colonnes = st.columns(PROPORTIONS_COLONNES, vertical_alignment="center")
        if en_confirmation:
            colonnes[0].markdown(
                f'<div class="table__principal">{escape(prestation.nom)}</div>'
                '<div class="table__secondaire table__secondaire--alerte">'
                "Suppression définitive, impossible à annuler après coup.</div>",
                unsafe_allow_html=True,
            )
        else:
            colonnes[0].markdown(
                cellule_double(prestation.nom, _precision_attributs(prestation)),
                unsafe_allow_html=True,
            )
        colonnes[1].markdown(f"<div>{pastille_categorie(prestation.categorie)}</div>", unsafe_allow_html=True)
        colonnes[2].markdown(
            f'<div class="table__secondaire">{libelle_unite(prestation.unite_facturation)}</div>',
            unsafe_allow_html=True,
        )
        colonnes[3].markdown(
            f'<div class="table__nb table__principal">'
            f"{formater_montant(prestation.prix_unitaire)}</div>",
            unsafe_allow_html=True,
        )
        if prestation.actif:
            if colonnes[4].button(
                "Modifier", key=f"modifier-{prestation.id}", use_container_width=True
            ):
                _ouvrir_formulaire(prestation.id)
            if colonnes[5].button(
                "Retirer", key=f"basculer-{prestation.id}", use_container_width=True
            ):
                _basculer(tenant, prestation)
        elif en_confirmation:
            if colonnes[4].button(
                "Confirmer", key=f"confirmer-suppression-{prestation.id}", type="primary",
                use_container_width=True,
            ):
                _supprimer(tenant, prestation)
            if colonnes[5].button(
                "Annuler", key=f"annuler-suppression-{prestation.id}", use_container_width=True
            ):
                st.session_state.pop(CLE_CONFIRMATION_SUPPRESSION, None)
                st.rerun()
        else:
            if colonnes[4].button(
                "Remettre", key=f"basculer-{prestation.id}", use_container_width=True
            ):
                _basculer(tenant, prestation)
            if colonnes[5].button(
                "Supprimer", key=f"supprimer-{prestation.id}", use_container_width=True
            ):
                st.session_state[CLE_CONFIRMATION_SUPPRESSION] = prestation.id
                st.rerun()


def _precision_attributs(prestation: RessourceGestion) -> str | None:
    """Sous-ligne d'une prestation : ses attributs, dans l'ordre du schéma"""
    valeurs = [
        str(prestation.attributs[champ.cle])
        for champ in champs_attributs(prestation.categorie)
        if prestation.attributs.get(champ.cle) not in (None, "")
    ]
    if not valeurs:
        return None
    if prestation.categorie == "salle" and len(valeurs) == 2:
        return f"{valeurs[1]} · {valeurs[0]} places"
    return " · ".join(valeurs)


def _afficher_formulaire(tenant: TenantContexte, reference: str) -> None:
    """Formulaire d'ajout ou de modification, selon la référence en session"""
    nouvelle = reference == NOUVELLE_PRESTATION
    prestation = None if nouvelle else _charger_prestation(tenant, reference)

    if not nouvelle and prestation is None:
        _fermer_formulaire("Cette prestation n'existe plus.", niveau=NIVEAU_ALERTE)
        return

    st.markdown(
        titre_ecran(
            "Ajouter une prestation" if nouvelle else f"Modifier « {prestation.nom} »",
            "Le prix saisi ici sera utilisé tel quel dans les prochaines estimations.",
        ),
        unsafe_allow_html=True,
    )

    with st.container(key="carte-formulaire"):
        categorie = st.selectbox(
            "Catégorie",
            CATEGORIES,
            index=CATEGORIES.index(prestation.categorie) if prestation else 0,
            format_func=lambda valeur: libelle_categorie(valeur).capitalize(),
            key=f"{PREFIXE_SAISIE}categorie",
            help="Détermine les précisions demandées ci-dessous.",
        )
        _suivre_la_categorie(categorie)
        with st.form("formulaire-prestation", border=False):
            saisie = _champs_du_formulaire(categorie, prestation)
            colonne_valider, colonne_annuler = st.columns(2)
            soumis = colonne_valider.form_submit_button(
                "Enregistrer",
                key="enregistrer-prestation",
                type="primary",
                use_container_width=True,
            )
            annule = colonne_annuler.form_submit_button(
                "Annuler", key="annuler-prestation", use_container_width=True
            )

    if annule:
        _fermer_formulaire()
    if soumis:
        _enregistrer(tenant, reference, saisie)


def _suivre_la_categorie(categorie: str) -> None:
    """Réinitialise les champs dépendants quand la catégorie change.

    L'unité de facturation et les attributs dépendent de la catégorie, mais la
    valeur mémorisée sous la clé d'un widget l'emporte sur la valeur initiale
    passée à sa construction : sans cette remise à zéro, passer de « salle » à
    « restauration » garderait « par jour » au lieu de proposer « par personne ».
    """
    categorie_vue = st.session_state.get(CLE_CATEGORIE_VUE)
    st.session_state[CLE_CATEGORIE_VUE] = categorie
    if categorie_vue is None or categorie_vue == categorie:
        return
    st.session_state.pop(f"{PREFIXE_SAISIE}unite", None)
    for cle in [
        cle for cle in st.session_state if cle.startswith(f"{PREFIXE_SAISIE}attribut-")
    ]:
        st.session_state.pop(cle, None)
    st.rerun()


def _champs_du_formulaire(
    categorie: str, prestation: RessourceGestion | None
) -> SaisieRessource:
    """Champs communs, puis ceux que la catégorie réclame (voir SCHEMA_ATTRIBUTS)"""
    nom = st.text_input(
        "Nom de la prestation",
        value=prestation.nom if prestation else "",
        placeholder="Salle des fêtes Le Bastos",
        key=f"{PREFIXE_SAISIE}nom",
    )
    colonne_unite, colonne_prix = st.columns(2)
    unite = colonne_unite.selectbox(
        "Unité de facturation",
        UNITES_FACTURATION,
        index=UNITES_FACTURATION.index(_unite_par_defaut(categorie, prestation)),
        format_func=libelle_unite,
        key=f"{PREFIXE_SAISIE}unite",
    )
    prix_unitaire = colonne_prix.number_input(
        "Prix unitaire (FCFA)",
        min_value=0,
        max_value=PRIX_MAXIMUM,
        step=PAS_DE_PRIX,
        value=prestation.prix_unitaire if prestation else None,
        placeholder="350000",
        key=f"{PREFIXE_SAISIE}prix",
        help="Montant entier en FCFA, sans virgule ni centime.",
    )

    # Un champ laissé vide n'entre pas dans le dictionnaire : mieux vaut une
    # clé absente qu'une clé à null, que le moteur devrait ensuite distinguer.
    attributs = {}
    for champ in champs_attributs(categorie):
        valeur = _champ_dattribut(champ, prestation)
        if valeur is not None:
            attributs[champ.cle] = valeur

    return SaisieRessource(
        nom=nom,
        categorie=categorie,
        unite_facturation=unite,
        prix_unitaire=int(prix_unitaire or 0),
        attributs=attributs,
    )


def _champ_dattribut(champ: ChampAttribut, prestation: RessourceGestion | None) -> int | str | None:
    """Un champ de saisie du type décrit par le schéma d'attributs.

    Renvoie None quand le champ est laissé vide, jamais zéro : un zéro serait
    une capacité saisie, alors qu'une absence doit être refusée par la
    validation (voir src/catalogue/edition.py).
    """
    valeur_connue = prestation.attributs.get(champ.cle) if prestation else None
    libelle = champ.libelle if champ.obligatoire else f"{champ.libelle} (facultatif)"
    cle = f"{PREFIXE_SAISIE}attribut-{champ.cle}"
    if champ.nature == "entier":
        saisi = st.number_input(
            libelle,
            min_value=0,
            value=int(valeur_connue) if valeur_connue else None,
            step=10,
            placeholder="300",
            key=cle,
            help=champ.aide,
        )
        return int(saisi) if saisi is not None else None
    saisi_texte = st.text_input(
        libelle, value=str(valeur_connue) if valeur_connue else "", key=cle, help=champ.aide
    )
    return saisi_texte.strip() or None


def _unite_par_defaut(categorie: str, prestation: RessourceGestion | None) -> str:
    """Unité de la prestation modifiée, ou celle qu'on facture d'habitude pour la catégorie"""
    if prestation and prestation.unite_facturation in UNITES_FACTURATION:
        return prestation.unite_facturation
    return UNITE_HABITUELLE.get(categorie, UNITES_FACTURATION[0])


def _charger_prestation(tenant: TenantContexte, ressource_id: str) -> RessourceGestion | None:
    """Prestation du tenant portant cet identifiant, None si elle ne lui appartient pas"""
    with ouvrir_session() as session:
        prestations = lister_pour_gestion(session, tenant.id)
    return next((une for une in prestations if une.id == ressource_id), None)


def _enregistrer(tenant: TenantContexte, reference: str, saisie: SaisieRessource) -> None:
    """Écrit la prestation si la saisie est acceptable, sinon affiche les refus"""
    raisons = valider_saisie(saisie)
    if raisons:
        for raison in raisons:
            st.error(raison)
        return

    with ouvrir_session() as session:
        if reference == NOUVELLE_PRESTATION:
            creer_ressource(session, tenant.id, saisie)
            _fermer_formulaire(f"« {saisie.nom} » a été ajoutée au catalogue.")
            return
        if not modifier_ressource(session, tenant.id, reference, saisie):
            _fermer_formulaire("Cette prestation n'existe plus.", niveau=NIVEAU_ALERTE)
            return
    _fermer_formulaire(f"« {saisie.nom} » a été mise à jour.")


def _basculer(tenant: TenantContexte, prestation: RessourceGestion) -> None:
    """Retire du catalogue ou remet en service, sans jamais supprimer la ligne"""
    with ouvrir_session() as session:
        basculer_activation(session, tenant.id, prestation.id)
    st.session_state.message_catalogue = (
        NIVEAU_SUCCES,
        f"« {prestation.nom} » n'est plus proposée aux prospects."
        if prestation.actif
        else f"« {prestation.nom} » est de nouveau proposée aux prospects.",
    )
    st.rerun()


def _supprimer(tenant: TenantContexte, prestation: RessourceGestion) -> None:
    """Efface définitivement une prestation déjà retirée, sur confirmation"""
    with ouvrir_session() as session:
        supprimer_ressource(session, tenant.id, prestation.id)
    st.session_state.pop(CLE_CONFIRMATION_SUPPRESSION, None)
    st.session_state.message_catalogue = (
        NIVEAU_SUCCES, f"« {prestation.nom} » a été supprimée définitivement."
    )
    st.rerun()


def _ouvrir_formulaire(reference: str) -> None:
    """Ouvre le formulaire sur une prestation, en oubliant la saisie précédente"""
    _oublier_saisie()
    st.session_state.ressource_en_edition = reference
    st.rerun()


def _fermer_formulaire(message: str | None = None, niveau: str = NIVEAU_SUCCES) -> None:
    """Revient à la liste, avec un message à afficher au prochain rendu"""
    _oublier_saisie()
    st.session_state.pop("ressource_en_edition", None)
    if message:
        st.session_state.message_catalogue = (niveau, message)
    st.rerun()


def _afficher_message() -> None:
    """Affiche le message laissé par l'action précédente, une seule fois.

    Une prestation introuvable n'est pas une réussite : le niveau distingue la
    confirmation de l'avertissement plutôt que de tout peindre en vert.
    """
    message = st.session_state.pop("message_catalogue", None)
    if message is None:
        return
    niveau, texte = message
    if niveau == NIVEAU_SUCCES:
        st.success(texte)
    else:
        st.warning(texte)


def _oublier_saisie() -> None:
    """Vide les champs du formulaire avant de le réafficher.

    Sans ça, Streamlit rendrait le formulaire avec les valeurs de la prestation
    précédemment ouverte : la valeur mémorisée sous la clé d'un widget
    l'emporte sur la valeur initiale passée à sa construction.
    """
    for cle in [cle for cle in st.session_state if cle.startswith(PREFIXE_SAISIE)]:
        st.session_state.pop(cle, None)


def _aucune_prestation(categorie: str) -> str:
    """État vide, distinguant un catalogue vide d'un filtre sans résultat"""
    if categorie != FILTRE_TOUTES:
        return etat_vide(
            f"Aucune prestation en {libelle_categorie(categorie)}",
            "Choisissez une autre catégorie, ou ajoutez une première prestation "
            "dans celle-ci.",
        )
    return etat_vide(
        "Votre catalogue est vide",
        "Une estimation ne peut rien chiffrer sans catalogue : ajoutez vos salles, "
        "puis vos prestations, avec leur prix et leur unité de facturation.",
    )
