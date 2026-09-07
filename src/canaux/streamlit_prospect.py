"""Écran de chat du prospect, canal Streamlit.

Ce module affiche et collecte, il ne décide rien. Le besoin est extrait par
la couche extraction, la question suivante est choisie par l'orchestrateur,
les montants sortent du moteur de devis. Aucun chiffre n'est calculé ici.

Lancement : streamlit run src/canaux/streamlit_prospect.py
puis ouvrir l'URL avec le slug du tenant, par exemple ?slug=etoile
"""
import base64
import sys
from dataclasses import replace
from html import escape
from pathlib import Path

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

# Permet de lancer ce fichier via « streamlit run » sans que la racine du
# projet soit déjà sur le sys.path (même besoin que data/seed/seed.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.canaux.tenant import extraire_slug_depuis_url, resoudre_tenant  # noqa: E402
from src.canaux.types import TenantContexte, TenantIndisponible  # noqa: E402
from src.catalogue.ressources import (  # noqa: E402
    charger_modele_evenement,
    charger_ressources_actives,
)
from src.db.session import ouvrir_session  # noqa: E402
from src.extraction.fabrique import (  # noqa: E402
    FOURNISSEUR_MOCK,
    construire_extracteur,
    fournisseur_actif,
)
from src.extraction.interface import InterfaceLLM  # noqa: E402
from src.extraction.mock import ExtracteurMock  # noqa: E402
from src.extraction.types import Besoin  # noqa: E402
from src.moteur.types import ResultatChiffrage, RessourceCatalogue  # noqa: E402
from src.orchestration.machine import decider_prochaine_etape  # noqa: E402
from src.orchestration.parcours import chiffrer_pour_besoin, resoudre_candidats  # noqa: E402
from src.orchestration.questions import (  # noqa: E402
    formuler_question_besoin,
    libelle_categorie,
)
from src.orchestration.types import (  # noqa: E402
    Decision,
    PassageChiffrage,
    QuestionBesoin,
    QuestionChoixRessources,
)
from src.pdf.generer_devis import generer_pdf_devis  # noqa: E402

NOM_MODELE_EVENEMENT = "Mariage"

# Dépose un fichier logo.svg ou logo.png ici pour qu'il remplace la pastille
# de repli en tête de la barre latérale, sans toucher au code (voir _logo_marque).
DOSSIER_ASSETS = Path(__file__).parent / "assets"
FORMATS_LOGO_ACCEPTES = {".svg": "image/svg+xml", ".png": "image/png"}

AGENT = "agent"
PROSPECT = "prospect"

LIBELLES_UNITES = {
    "jour": "par jour",
    "unite": "l'unité",
    "personne": "par personne",
    "forfait": "au forfait",
    "heure": "par heure",
}

MESSAGES_ACCES_REFUSE = {
    "slug_absent": (
        "Ce lien ne précise pas l'entreprise",
        "Demandez à l'organisateur le lien complet vers son espace d'estimation.",
    ),
    "slug_inconnu": (
        "Ce lien ne correspond à aucune entreprise",
        "Vérifiez l'adresse reçue : elle a peut-être été tronquée.",
    ),
    "tenant_inactif": (
        "Cet espace d'estimation est fermé",
        "L'entreprise a suspendu son service d'estimation en ligne.",
    ),
}

# Réponses d'extraction prédéfinies : chaque message du prospect consomme la
# suivante. Aucun appel réseau, donc un parcours reproductible de bout en bout.
# ExtracteurGroq remplacera ce mock une fois le parcours validé.
SCENARIOS_DEMONSTRATION: dict[str, list[Besoin]] = {
    "300 invités, Bastos": [
        Besoin(type_evenement="mariage"),
        Besoin(
            type_evenement="mariage",
            nombre_invites=300,
            ville="Yaoundé",
            quartier_souhaite="Bastos",
        ),
        Besoin(
            type_evenement="mariage",
            date_evenement="2026-12-12",
            ville="Yaoundé",
            quartier_souhaite="Bastos",
            nombre_invites=300,
            duree_jours=1,
        ),
        # Un message de plus une fois le besoin complet (« merci », par
        # exemple) : le fournisseur réel renverrait le même besoin déjà connu,
        # sans ressources_choisies puisque ce champ n'existe pas dans son
        # schéma. Ce quatrième besoin le reproduit fidèlement pour la
        # démonstration comme pour les tests.
        Besoin(
            type_evenement="mariage",
            date_evenement="2026-12-12",
            ville="Yaoundé",
            quartier_souhaite="Bastos",
            nombre_invites=300,
            duree_jours=1,
        ),
    ],
    "900 invités, salle insuffisante": [
        Besoin(type_evenement="mariage", nombre_invites=900),
        Besoin(
            type_evenement="mariage",
            date_evenement="2026-07-04",
            ville="Yaoundé",
            quartier_souhaite="Bastos",
            nombre_invites=900,
            duree_jours=2,
        ),
    ],
}

FEUILLE_DE_STYLE = """
<style>
/* Palette Kaeyros : bleu #0f2a96 et orange #ff5f00. L'orange descend à
   #d94f00 dès qu'il porte du texte sur fond blanc, pour rester lisible. */
:root{
  --bleu:#0f2a96; --bleu-fonce:#0a1f6f; --bleu-pale:#eaeefb; --bleu-pale-vif:#dde4f9;
  --orange:#ff5f00; --orange-texte:#d94f00; --orange-pale:#fff1e6; --orange-pale-vif:#ffe1cc;
  --encre:#101322; --gris:#5b6178; --trait:#e2e6f2;
  --surface:#ffffff; --fond:#f4f5fb;
}

/* Fond teinté aux deux couleurs de marque plutôt qu'un gris plat, sur toute
   la hauteur de la page et pas seulement les premiers écrans. */
.stApp{
  background:
    radial-gradient(1300px 900px at 6% -10%, rgba(15,42,150,.14), transparent 62%),
    radial-gradient(1100px 780px at 104% 2%, rgba(255,95,0,.12), transparent 58%),
    radial-gradient(1400px 900px at 50% 130%, rgba(15,42,150,.07), transparent 65%),
    var(--fond);
  background-attachment:fixed;
}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none;}
/* stHeader garde un fond opaque par défaut : sans cette ligne, une bande
   blanche reste visible au-dessus de l'en-tête malgré le dégradé de fond. */
[data-testid="stHeader"]{background:transparent;}
.stMainBlockContainer, .block-container{max-width:820px;padding-top:1.8rem;padding-bottom:8rem;}
*{overflow-wrap:break-word;}

.entete{background:linear-gradient(135deg,var(--bleu) 0%,var(--bleu-fonce) 100%);
  border-radius:20px;padding:1.5rem 1.7rem;color:#fff;box-shadow:0 14px 34px rgba(15,42,150,.22);
  position:relative;overflow:hidden;}
.entete::after{content:"";position:absolute;inset:0 0 auto auto;width:220px;height:220px;
  background:radial-gradient(circle,rgba(255,95,0,.35),transparent 70%);
  transform:translate(35%,-45%);}
.entete__kicker{position:relative;font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;
  color:#c3cdf5;font-weight:700;}
.entete__nom{position:relative;font-size:1.55rem;font-weight:700;margin:.2rem 0 .55rem;line-height:1.25;}
.entete__filet{position:relative;width:56px;height:4px;border-radius:2px;background:var(--orange);}
.entete__sous{position:relative;font-size:.9rem;color:#d7ddf7;margin-top:.7rem;line-height:1.55;
  max-width:34rem;}

/* Étapes en pastilles pleines plutôt qu'un simple filet : plus de couleur, plus lisible */
.etapes{display:flex;gap:.5rem;margin:1.3rem 0 .3rem;}
.etape{flex:1;display:flex;align-items:center;gap:.5rem;font-size:.78rem;color:var(--gris);
  background:var(--surface);border:1px solid var(--trait);border-radius:999px;
  padding:.4rem .85rem .4rem .4rem;font-weight:600;}
.etape__puce{flex:none;width:1.55rem;height:1.55rem;border-radius:50%;background:#eceef6;
  color:var(--gris);font-size:.72rem;font-weight:800;display:flex;align-items:center;
  justify-content:center;}
.etape--faite{color:var(--orange-texte);background:var(--orange-pale);border-color:#ffd7b8;}
.etape--faite .etape__puce{background:var(--orange);color:#fff;}
.etape--active{color:var(--bleu);background:var(--bleu-pale);border-color:#c7d1f6;}
.etape--active .etape__puce{background:var(--bleu);color:#fff;}

.fil{display:flex;flex-direction:column;gap:.65rem;margin:1.3rem 0 .4rem;}
.bulle{max-width:84%;padding:.8rem 1.05rem;border-radius:16px;font-size:.95rem;line-height:1.55;}
.bulle--agent{background:var(--surface);border:1px solid var(--trait);border-left:3px solid var(--bleu);
  border-top-left-radius:5px;align-self:flex-start;color:var(--encre);
  box-shadow:0 2px 8px rgba(16,19,34,.05);}
.bulle--prospect{background:linear-gradient(135deg,var(--bleu),var(--bleu-fonce));color:#fff;
  border-top-right-radius:5px;align-self:flex-end;box-shadow:0 4px 14px rgba(15,42,150,.22);}
.bulle__auteur{display:block;font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
  opacity:.65;margin-bottom:.3rem;font-weight:700;}

/* Indicateur de frappe pendant l'appel au fournisseur, à la place d'un texte
   du type « Je vous écoute » : trois points qui rebondissent, comme la
   plupart des interfaces de conversation. */
.frappe{display:inline-flex;gap:.28rem;align-items:center;padding:.15rem 0;}
.frappe span{width:.4rem;height:.4rem;border-radius:50%;background:var(--gris);
  opacity:.4;animation:frappe-rebond 1.1s infinite ease-in-out;}
.frappe span:nth-child(2){animation-delay:.15s;}
.frappe span:nth-child(3){animation-delay:.3s;}
@keyframes frappe-rebond{
  0%,80%,100%{opacity:.35;transform:translateY(0);}
  40%{opacity:1;transform:translateY(-3px);}
}

.invite{font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--bleu);
  margin:1.3rem 0 .6rem;font-weight:800;}

/* Cartes de choix : padding réel, accent de marque, aération. Sans le padding
   sur la ligne de colonnes, le texte touchait le bord de la carte et donnait
   une impression de débordement. */
[class*="st-key-option-"]{background:var(--surface);border:1px solid var(--trait);
  border-left:4px solid var(--orange);border-radius:14px;
  box-shadow:0 2px 10px rgba(16,19,34,.05);margin-bottom:.65rem;overflow:hidden;
  transition:box-shadow .15s ease;}
[class*="st-key-option-"]:hover{box-shadow:0 8px 24px rgba(16,19,34,.10);}
[class*="st-key-option-"] [data-testid="stVerticalBlockBorderWrapper"]{border:none;box-shadow:none;
  background:transparent;}
/* !important : le conteneur de colonnes de Streamlit porte parfois un padding
   inline (via le réglage "gap"), qui l'emporterait sinon sur cette règle et
   laisserait le texte revenir au bord de la carte. */
[class*="st-key-option-"] [data-testid="stHorizontalBlock"]{padding:1.05rem 1.2rem !important;
  align-items:center !important;gap:1rem !important;}
[class*="st-key-option-"] [data-testid="stColumn"]{padding:0 !important;}
[class*="st-key-option-"] .stButton>button{background:var(--bleu);color:#fff;border:none;
  border-radius:10px;font-weight:700;padding:.6rem 0;}
[class*="st-key-option-"] .stButton>button:hover{background:var(--bleu-fonce);color:#fff;}

/* Bouton de refus d'une catégorie : discret, jamais en concurrence visuelle
   avec les cartes « Choisir ». */
[class*="st-key-exclure-"] button{background:transparent;color:var(--gris);
  border:1px dashed var(--trait);border-radius:10px;font-weight:600;box-shadow:none;
  margin-top:.2rem;}
[class*="st-key-exclure-"] button:hover{color:var(--orange-texte);
  border-color:#ffd7b8;background:var(--orange-pale);}

.option__nom{font-weight:700;color:var(--encre);font-size:1rem;line-height:1.35;}
.option__prix{color:var(--bleu);font-weight:800;font-variant-numeric:tabular-nums;
  font-size:1rem;margin-top:.25rem;}
.option__unite{color:var(--gris);font-weight:500;font-size:.8rem;}
.option__badges{margin-top:.5rem;display:flex;flex-wrap:wrap;gap:.35rem;}
.badge{display:inline-flex;align-items:center;font-size:.72rem;padding:.2rem .6rem;
  border-radius:999px;white-space:nowrap;font-weight:600;}
.badge--neutre{background:#eef0f8;color:var(--gris);}
.badge--quartier{background:var(--orange-pale-vif);color:var(--orange-texte);font-weight:700;}

.devis{background:var(--surface);border:1px solid var(--trait);border-top:4px solid var(--orange);
  border-radius:20px;overflow:hidden;box-shadow:0 12px 34px rgba(16,19,34,.10);margin-top:.7rem;}
.devis__entete{padding:1.2rem 1.3rem .9rem;border-bottom:1px solid var(--trait);}
.devis__kicker{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:var(--orange-texte);
  font-weight:800;}
.devis__titre{font-size:1.15rem;font-weight:700;color:var(--bleu);margin-top:.2rem;}
.devis__resume{font-size:.85rem;color:var(--gris);margin-top:.25rem;}
.devis__defilement{overflow-x:auto;}
.devis__table{width:100%;border-collapse:collapse;font-size:.9rem;}
.devis__table th{text-align:left;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--bleu-fonce);padding:.65rem 1.3rem;background:var(--bleu-pale);font-weight:800;}
.devis__table td{padding:.7rem 1.3rem;border-top:1px solid var(--trait);color:var(--encre);}
.devis__table tbody tr:nth-child(even){background:#fbfbfe;}
.devis__nb{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
.devis__total{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;
  padding:1.1rem 1.3rem;background:linear-gradient(135deg,var(--bleu-pale),var(--bleu-pale-vif));}
.devis__total-libelle{font-weight:700;color:var(--bleu-fonce);letter-spacing:.02em;}
.devis__total-montant{font-size:1.55rem;font-weight:800;color:var(--orange-texte);
  font-variant-numeric:tabular-nums;white-space:nowrap;}
.devis__mention{font-size:.75rem;color:var(--gris);padding:.8rem 1.3rem;
  border-top:1px dashed var(--trait);line-height:1.5;}

.panneau{border-radius:14px;padding:.95rem 1.15rem;font-size:.88rem;margin-top:.8rem;
  border:1px solid;line-height:1.55;}
.panneau--alerte{background:var(--orange-pale);border-color:#ffd6bb;color:#7a3200;}
.panneau--info{background:var(--bleu-pale);border-color:#c7d1f6;color:var(--bleu-fonce);}
.panneau__titre{font-weight:700;margin-bottom:.25rem;}

.arret{background:var(--surface);border:1px solid var(--trait);border-radius:20px;
  padding:2.4rem 1.8rem;text-align:center;box-shadow:0 12px 34px rgba(16,19,34,.10);margin-top:3rem;}
.arret__icone{width:54px;height:54px;margin:0 auto 1.1rem;border-radius:50%;
  background:linear-gradient(135deg,var(--orange-pale-vif),var(--orange-pale));
  color:var(--orange-texte);display:flex;align-items:center;justify-content:center;
  font-size:1.5rem;font-weight:800;}
.arret__titre{font-size:1.2rem;font-weight:700;color:var(--bleu);}
.arret__texte{font-size:.92rem;color:var(--gris);margin-top:.5rem;line-height:1.6;}

/* Marque en tête de panneau latéral : le logo remplace la pastille dès
   qu'un fichier est déposé dans src/canaux/assets/ (voir _logo_marque). */
.marque{display:flex;align-items:center;gap:.55rem;margin-bottom:1.2rem;}
.marque__pastille{width:1.5rem;height:1.5rem;border-radius:8px;flex:none;
  background:linear-gradient(135deg,var(--bleu) 50%,var(--orange) 50%);}
.marque__logo{height:1.7rem;width:auto;flex:none;}
.marque__nom{font-weight:800;color:var(--bleu-fonce);letter-spacing:.02em;font-size:1.02rem;}

section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--bleu-pale) 0%,var(--fond) 260px);
  border-right:1px solid var(--trait);min-width:280px !important;}
[class*="st-key-panneau-"]{background:var(--surface);border:1px solid var(--trait);
  border-radius:16px;padding:1.05rem 1.1rem;box-shadow:0 2px 10px rgba(16,19,34,.05);
  margin-bottom:.75rem;}
[class*="st-key-panneau-demo"]{padding-bottom:.3rem;}
.demo__titre{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--orange-texte);
  font-weight:800;margin-bottom:.3rem;}

/* Récapitulatif du besoin en barre latérale : un repère pour le prospect,
   pas un outil de débogage — aucun détail d'implémentation n'y figure. */
.recap__ligne{display:flex;justify-content:space-between;gap:.75rem;font-size:.83rem;
  padding:.4rem 0;border-bottom:1px dashed var(--trait);}
.recap__ligne:last-child{border-bottom:none;padding-bottom:0;}
.recap__ligne:first-child{padding-top:0;}
.recap__cle{color:var(--gris);font-weight:600;}
.recap__valeur{color:var(--bleu-fonce);font-weight:700;text-align:right;}
.recap__valeur--manquant{color:#b6bccd;font-weight:500;}

[data-testid="stChatInput"]{border-radius:16px;}
</style>
"""


def main() -> None:
    """Rend l'écran complet pour un tour de conversation"""
    _configurer_page()
    try:
        tenant = _resoudre_tenant_ou_bloquer()
        _charger_catalogue_du_tenant(tenant)
    except SQLAlchemyError:
        _afficher_arret(
            "Service momentanément indisponible",
            "Le catalogue de l'entreprise est injoignable. Réessayez dans quelques instants.",
        )
        st.stop()

    _initialiser_conversation_si_absente(tenant)
    _afficher_panneau_lateral(tenant)

    if st.session_state.modele is None:
        _afficher_arret(
            "Estimation indisponible",
            "Cette entreprise n'a pas encore configuré de modèle d'événement.",
        )
        st.stop()

    decision = _decider()
    _afficher_entete(tenant)
    _afficher_etapes(decision)
    _afficher_fil()
    _afficher_suite(decision, tenant)

    message = st.chat_input("Décrivez votre événement…")
    if message:
        _traiter_message_prospect(message)
        st.rerun()


def _configurer_page() -> None:
    """Fixe le gabarit de la page et charge la feuille de style"""
    st.set_page_config(page_title="Estimation en ligne", layout="centered")
    st.markdown(FEUILLE_DE_STYLE, unsafe_allow_html=True)


def _resoudre_tenant_ou_bloquer() -> TenantContexte:
    """Résout le tenant depuis l'URL, ou affiche un écran d'arrêt et stoppe le rendu"""
    with ouvrir_session() as session:
        resolution = resoudre_tenant(session, extraire_slug_depuis_url())

    if isinstance(resolution, TenantIndisponible):
        titre, texte = MESSAGES_ACCES_REFUSE[resolution.raison]
        _afficher_arret(titre, texte)
        st.stop()

    return resolution.tenant


def _charger_catalogue_du_tenant(tenant: TenantContexte) -> None:
    """Charge le catalogue et le modèle d'événement du tenant, une fois par tenant.

    Le slug de l'URL peut changer sans que la session Streamlit change : le
    catalogue est donc rechargé et la conversation repartie de zéro dès que le
    tenant diffère, pour qu'aucune donnée d'une entreprise n'en atteigne une autre.
    """
    if "tenant" in st.session_state and st.session_state.tenant.id == tenant.id:
        return
    with ouvrir_session() as session:
        st.session_state.catalogue = charger_ressources_actives(session, tenant.id)
        st.session_state.modele = charger_modele_evenement(
            session, tenant.id, NOM_MODELE_EVENEMENT
        )
    st.session_state.tenant = tenant
    st.session_state.pop("besoin", None)


def _initialiser_conversation_si_absente(tenant: TenantContexte) -> None:
    """Ouvre la conversation au premier passage, sans écraser un état existant"""
    if "besoin" in st.session_state:
        return
    _reinitialiser_conversation(tenant, next(iter(SCENARIOS_DEMONSTRATION)))


def _reinitialiser_conversation(tenant: TenantContexte, nom_scenario: str) -> None:
    """Repart d'un besoin vide et d'un extracteur neuf"""
    st.session_state.besoin = Besoin()
    st.session_state.extracteur = _extracteur_de_la_conversation(nom_scenario)
    st.session_state.scenario_actif = nom_scenario
    st.session_state.historique = [
        (
            AGENT,
            f"Bonjour, je prépare votre estimation pour {tenant.nom}. "
            "Décrivez-moi votre événement : le type, la date, la ville, "
            "le nombre d'invités et la durée.",
        )
    ]


def _extracteur_de_la_conversation(nom_scenario: str) -> InterfaceLLM:
    """Extracteur du fournisseur configuré dans LLM_PROVIDER.

    Seul le mock reçoit un scénario : ne consultant aucun modèle, il n'a que
    ces réponses préparées pour faire avancer le besoin. Les fournisseurs
    réels lisent les messages du prospect, il n'y a rien à leur souffler.
    """
    if fournisseur_actif() == FOURNISSEUR_MOCK:
        return ExtracteurMock(besoins_a_renvoyer=list(SCENARIOS_DEMONSTRATION[nom_scenario]))
    return construire_extracteur()


def _decider() -> Decision:
    """Recalcule la décision courante à partir du besoin et du catalogue"""
    besoin = st.session_state.besoin
    candidats = resoudre_candidats(besoin, st.session_state.catalogue, st.session_state.modele)
    return decider_prochaine_etape(besoin, candidats)


def _traiter_message_prospect(message: str) -> None:
    """Enregistre le message, met à jour le besoin, puis fait répondre l'agent.

    L'attente est visible : avec un fournisseur réel, ce tour de conversation
    tient deux appels réseau, l'extraction puis la reformulation.
    """
    st.session_state.historique.append((PROSPECT, message))
    espace_frappe = st.empty()
    espace_frappe.markdown(
        '<div class="fil"><div class="bulle bulle--agent">'
        '<span class="bulle__auteur">Estimate</span>'
        '<div class="frappe"><span></span><span></span><span></span></div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
    besoin_avant = st.session_state.besoin
    besoin_extrait = st.session_state.extracteur.extraire_besoin(message, besoin_avant)
    # ressources_choisies n'existe pas dans le schéma JSON de l'extracteur : ce
    # champ n'est jamais lu ni écrit par le LLM (D04), seulement par les clics
    # du prospect. Sans cette ligne, le premier message envoyé après un choix
    # de ressource l'effacerait silencieusement, puisque le Besoin reconstruit
    # par l'extracteur repart toujours d'une liste vide.
    st.session_state.besoin = replace(
        besoin_extrait, ressources_choisies=besoin_avant.ressources_choisies
    )
    _repondre()
    espace_frappe.empty()


def _enregistrer_choix(ressource: RessourceCatalogue) -> None:
    """Ajoute la ressource choisie au besoin, puis fait répondre l'agent"""
    besoin = st.session_state.besoin
    st.session_state.besoin = replace(
        besoin, ressources_choisies=besoin.ressources_choisies + (ressource.id,)
    )
    st.session_state.historique.append((PROSPECT, f"Je retiens : {ressource.nom}"))
    _repondre()


def _exclure_categorie(categorie: str) -> None:
    """Retire une catégorie du besoin : le prospect n'en veut pas, le moteur ne la chiffrera pas"""
    besoin = st.session_state.besoin
    st.session_state.besoin = replace(
        besoin, prestations_exclues=besoin.prestations_exclues + (categorie,)
    )
    st.session_state.historique.append(
        (PROSPECT, f"Je ne veux pas de {libelle_categorie(categorie)}")
    )
    _repondre()


def _repondre() -> None:
    """Ajoute au fil la réponse de l'agent à l'état courant du besoin"""
    st.session_state.historique.append((AGENT, _formuler_reponse(_decider())))


def _formuler_reponse(decision: Decision) -> str:
    """Traduit la décision de l'orchestrateur en une phrase adressée au prospect.

    Seule la question sur le besoin passe par le LLM, pour être reformulée en
    français naturel. Le choix d'une ressource se fait par sélection directe
    dans le canal, sans appel au modèle (voir D04).
    """
    if isinstance(decision, QuestionBesoin):
        contenu = formuler_question_besoin(decision.champs_manquants)
        return st.session_state.extracteur.reformuler(contenu)
    if isinstance(decision, QuestionChoixRessources):
        return (
            f"Plusieurs options de {libelle_categorie(decision.categorie)} "
            "conviennent à votre événement. Laquelle retenez-vous ?"
        )
    return "J'ai tout ce qu'il me faut. Voici votre estimation."


def _afficher_entete(tenant: TenantContexte) -> None:
    """En-tête aux couleurs du produit, au nom de l'entreprise cliente (D14)"""
    st.markdown(
        f"""<div class="entete">
          <div class="entete__kicker">Estimation en ligne</div>
          <div class="entete__nom">{escape(tenant.nom)}</div>
          <div class="entete__filet"></div>
          <div class="entete__sous">Décrivez votre événement, je vous propose une
          estimation chiffrée à partir du catalogue de l'entreprise.</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _afficher_etapes(decision: Decision) -> None:
    """Repère de progression : besoin, choix, estimation"""
    if isinstance(decision, QuestionBesoin):
        rang_actif = 0
    elif isinstance(decision, QuestionChoixRessources):
        rang_actif = 1
    else:
        rang_actif = 2

    libelles = ("Votre besoin", "Vos choix", "Votre estimation")
    etapes = "".join(
        f'<div class="etape {_classe_etape(rang, rang_actif)}">'
        f'<span class="etape__puce">{"✓" if rang < rang_actif else rang + 1}</span>'
        f"{libelle}</div>"
        for rang, libelle in enumerate(libelles)
    )
    st.markdown(f'<div class="etapes">{etapes}</div>', unsafe_allow_html=True)


def _classe_etape(rang: int, rang_actif: int) -> str:
    """Classe CSS d'une étape selon sa position par rapport à l'étape courante"""
    if rang < rang_actif:
        return "etape--faite"
    if rang == rang_actif:
        return "etape--active"
    return ""


def _afficher_fil() -> None:
    """Affiche l'historique de la conversation, contenu échappé"""
    bulles = "".join(
        f'<div class="bulle bulle--{role}">'
        f'<span class="bulle__auteur">{"Vous" if role == PROSPECT else "Estimate"}</span>'
        f"{escape(texte)}</div>"
        for role, texte in st.session_state.historique
    )
    st.markdown(f'<div class="fil">{bulles}</div>', unsafe_allow_html=True)


def _afficher_suite(decision: Decision, tenant: TenantContexte) -> None:
    """Affiche ce que la décision appelle : un choix à faire, ou l'estimation"""
    if isinstance(decision, QuestionChoixRessources):
        _afficher_options(decision)
    elif isinstance(decision, PassageChiffrage):
        _afficher_devis(
            chiffrer_pour_besoin(
                st.session_state.besoin, st.session_state.catalogue, st.session_state.modele
            ),
            tenant,
        )


def _afficher_options(decision: QuestionChoixRessources) -> None:
    """Présente les ressources candidates, le prospect tranche (D03) — ou n'en veut aucune"""
    st.markdown(
        f'<p class="invite">Choisissez votre {libelle_categorie(decision.categorie)}</p>',
        unsafe_allow_html=True,
    )
    quartier_souhaite = st.session_state.besoin.quartier_souhaite
    for candidat in decision.candidats:
        with st.container(key=f"option-{candidat.id}"):
            colonne_infos, colonne_action = st.columns([3, 1], vertical_alignment="center")
            colonne_infos.markdown(
                _carte_option(candidat, quartier_souhaite), unsafe_allow_html=True
            )
            if colonne_action.button(
                "Choisir", key=f"choix-{candidat.id}", use_container_width=True
            ):
                _enregistrer_choix(candidat)
                st.rerun()

    if st.button(
        f"Je ne veux pas de {libelle_categorie(decision.categorie)}",
        key=f"exclure-{decision.categorie}",
    ):
        _exclure_categorie(decision.categorie)
        st.rerun()


def _carte_option(ressource: RessourceCatalogue, quartier_souhaite: str | None) -> str:
    """Nom, prix et repères d'une ressource candidate"""
    unite = LIBELLES_UNITES.get(ressource.unite_facturation, ressource.unite_facturation)
    return (
        f'<div class="option__nom">{escape(ressource.nom)}</div>'
        f'<div class="option__prix">{_formater_montant(ressource.prix_unitaire)} '
        f'<span class="option__unite">{escape(unite)}</span></div>'
        f'<div class="option__badges">{_badges_option(ressource, quartier_souhaite)}</div>'
    )


def _badges_option(ressource: RessourceCatalogue, quartier_souhaite: str | None) -> str:
    """Repères d'une salle : capacité et quartier.

    Une salle d'un autre quartier est proposée, jamais écartée (D17) : le
    badge dit lequel, pour que la liste reste lisible.
    """
    capacite = ressource.attributs.get("capacite")
    quartier = ressource.attributs.get("quartier")
    badges = []
    if capacite is not None:
        badges.append(f'<span class="badge badge--neutre">{capacite} places</span>')
    if quartier is not None:
        classe = "badge--quartier" if quartier == quartier_souhaite else "badge--neutre"
        badges.append(f'<span class="badge {classe}">{escape(str(quartier))}</span>')
    return "".join(badges)


def _afficher_devis(resultat: ResultatChiffrage, tenant: TenantContexte) -> None:
    """Présente l'estimation, ou explique pourquoi elle ne peut pas être établie"""
    besoin = st.session_state.besoin
    if not resultat.lignes:
        _afficher_impasse(resultat)
        return

    lignes = "".join(
        f"<tr><td>{escape(ligne.designation)}</td>"
        f'<td class="devis__nb">{ligne.quantite}</td>'
        f'<td class="devis__nb">{_formater_montant(ligne.prix_unitaire)}</td>'
        f'<td class="devis__nb">{_formater_montant(ligne.montant)}</td></tr>'
        for ligne in resultat.lignes
    )
    st.markdown(
        f"""<div class="devis">
          <div class="devis__entete">
            <div class="devis__kicker">Estimation</div>
            <div class="devis__titre">{escape(tenant.nom)}</div>
            <div class="devis__resume">{besoin.nombre_invites} invités &middot;
              {besoin.duree_jours} jour(s) &middot; {escape(besoin.ville or "")}</div>
          </div>
          <div class="devis__defilement">
            <table class="devis__table">
              <thead><tr><th>Prestation</th><th class="devis__nb">Qté</th>
                <th class="devis__nb">Prix unitaire</th><th class="devis__nb">Montant</th></tr></thead>
              <tbody>{lignes}</tbody>
            </table>
          </div>
          <div class="devis__total">
            <span class="devis__total-libelle">Total estimé</span>
            <span class="devis__total-montant">{_formater_montant(resultat.total)}</span>
          </div>
          <div class="devis__mention">Estimation indicative, non contractuelle,
            établie à partir du catalogue de {escape(tenant.nom)}.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    _afficher_bouton_telechargement(resultat, tenant, besoin)

    _afficher_categories_non_satisfaites(resultat)
    _afficher_alerte_budget(resultat, besoin)


def _afficher_bouton_telechargement(
    resultat: ResultatChiffrage, tenant: TenantContexte, besoin: Besoin
) -> None:
    """Bouton de téléchargement du devis en PDF, mis en forme par src/pdf (D14)"""
    st.download_button(
        "Télécharger le PDF",
        data=generer_pdf_devis(resultat, tenant, besoin),
        file_name=f"devis-{tenant.slug}.pdf",
        mime="application/pdf",
        key="telecharger-pdf",
    )


def _afficher_impasse(resultat: ResultatChiffrage) -> None:
    """Aucune ligne chiffrable : on l'annonce, on n'affiche pas un total à zéro"""
    _afficher_panneau(
        "alerte",
        "Aucune prestation disponible pour cette demande",
        "Aucune ressource du catalogue ne correspond à votre événement. "
        "Un conseiller peut vous répondre directement : laissez-lui vos coordonnées "
        "dans la conversation.",
    )
    _afficher_categories_non_satisfaites(resultat)


def _afficher_categories_non_satisfaites(resultat: ResultatChiffrage) -> None:
    """Annonce les catégories que le catalogue ne couvre pas, sans rien inventer"""
    if not resultat.categories_non_satisfaites:
        return

    besoin = st.session_state.besoin
    manquantes = [
        libelle_categorie(categorie.categorie)
        for categorie in resultat.categories_non_satisfaites
    ]
    detail = ""
    if any(categorie.categorie == "salle" for categorie in resultat.categories_non_satisfaites):
        detail = (
            f" Aucune salle du catalogue ne peut accueillir {besoin.nombre_invites} invités."
        )
    _afficher_panneau(
        "alerte",
        f"Non chiffré : {', '.join(manquantes)}",
        f"Ces prestations ne figurent pas dans l'estimation.{detail} "
        "Un conseiller peut étudier votre demande et vous proposer une solution.",
    )


def _afficher_alerte_budget(resultat: ResultatChiffrage, besoin: Besoin) -> None:
    """Signale le dépassement du budget déclaré, sans jamais baisser un prix"""
    if not resultat.depasse_budget:
        return
    _afficher_panneau(
        "info",
        "Au-dessus du budget que vous avez indiqué",
        f"Votre budget déclaré est de {_formater_montant(besoin.budget_declare or 0)}. "
        "Vous pouvez retirer des prestations ou choisir des options moins onéreuses.",
    )


def _afficher_panneau(variante: str, titre: str, texte: str) -> None:
    """Encart d'information ou d'alerte sous l'estimation"""
    st.markdown(
        f'<div class="panneau panneau--{variante}">'
        f'<div class="panneau__titre">{escape(titre)}</div>{escape(texte)}</div>',
        unsafe_allow_html=True,
    )


def _afficher_arret(titre: str, texte: str) -> None:
    """Écran affiché quand la conversation ne peut pas démarrer"""
    st.markdown(
        f"""<div class="arret">
          <div class="arret__icone">!</div>
          <div class="arret__titre">{escape(titre)}</div>
          <div class="arret__texte">{escape(texte)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _logo_marque() -> str:
    """Balisage du logo si un fichier est présent, sinon la pastille de repli.

    Pour afficher un vrai logo : déposer un fichier logo.svg ou logo.png dans
    src/canaux/assets/ (voir DOSSIER_ASSETS). Rien d'autre à modifier, le
    fichier est détecté au prochain chargement de la page.
    """
    for suffixe, type_mime in FORMATS_LOGO_ACCEPTES.items():
        chemin = DOSSIER_ASSETS / f"logo{suffixe}"
        if chemin.is_file():
            contenu_encode = base64.b64encode(chemin.read_bytes()).decode()
            return f'<img class="marque__logo" src="data:{type_mime};base64,{contenu_encode}" alt="Logo">'
    return '<span class="marque__pastille"></span>'


def _afficher_panneau_lateral(tenant: TenantContexte) -> None:
    """Panneau latéral : sélecteur de scénario en mock, récapitulatif du besoin sinon"""
    scenario = st.session_state.scenario_actif
    with st.sidebar:
        st.markdown(
            f'<div class="marque">{_logo_marque()}<span class="marque__nom">Estimate</span></div>',
            unsafe_allow_html=True,
        )
        if fournisseur_actif() == FOURNISSEUR_MOCK:
            with st.container(key="panneau-demo"):
                scenario = _afficher_reglages_mock()

        with st.container(key="panneau-recap"):
            _afficher_recapitulatif_besoin()

        recommencer = st.button("Recommencer", use_container_width=True)

    if recommencer or scenario != st.session_state.scenario_actif:
        _reinitialiser_conversation(tenant, scenario)
        st.rerun()


def _afficher_reglages_mock() -> str:
    """Réglages du mode démonstration, renvoie le scénario choisi"""
    st.markdown('<p class="demo__titre">Mode démonstration</p>', unsafe_allow_html=True)
    st.caption(
        "L'extraction est simulée, sans appel réseau : le mock rejoue un "
        "scénario préparé, quels que soient vos messages."
    )
    return st.selectbox("Scénario joué", list(SCENARIOS_DEMONSTRATION), key="scenario")


def _afficher_recapitulatif_besoin() -> None:
    """Récapitulatif du besoin déjà connu : un repère pour le prospect, pas un outil de débogage"""
    st.markdown('<p class="demo__titre">Votre événement</p>', unsafe_allow_html=True)
    besoin = st.session_state.besoin
    champs = (
        ("Type", besoin.type_evenement),
        ("Date", besoin.date_evenement),
        ("Ville", besoin.ville),
        ("Quartier", besoin.quartier_souhaite),
        ("Invités", besoin.nombre_invites),
        ("Durée", f"{besoin.duree_jours} jour(s)" if besoin.duree_jours else None),
    )
    lignes = "".join(
        f'<div class="recap__ligne"><span class="recap__cle">{cle}</span>'
        + (
            f'<span class="recap__valeur">{escape(str(valeur))}</span>'
            if valeur is not None
            else '<span class="recap__valeur recap__valeur--manquant">à préciser</span>'
        )
        + "</div>"
        for cle, valeur in champs
    )
    st.markdown(lignes, unsafe_allow_html=True)


def _formater_montant(montant: int) -> str:
    """Montant en FCFA, entier, devise explicite, espaces insécables.

    Les séparateurs sont des espaces insécables : un montant ne doit jamais
    se couper en fin de ligne.
    """
    return f"{montant:,}".replace(",", " ") + " FCFA"


if __name__ == "__main__":
    main()
