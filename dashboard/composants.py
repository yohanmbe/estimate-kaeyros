"""Fragments HTML du tableau de bord, sans aucun appel à Streamlit.

Ces fonctions sont pures : elles reçoivent des données et renvoient une chaîne.
Elles se testent donc sans lancer d'écran, et un test peut vérifier qu'un nom
de prospect n'échappe pas à html.escape — les pages sont rendues en
unsafe_allow_html, et un nom est une saisie libre venue d'Internet.

Aucun montant n'est calculé ici : les entiers arrivent déjà chiffrés par le
moteur ou relus dans un devis figé (D01, D11).
"""
from datetime import datetime
from html import escape

from src.catalogue.vocabulaire import libelle_categorie
from src.consultation.types import DevisConsulte, LigneListeDemande
from src.db.models import ETAT_ABANDONNEE, ETAT_COMPLETE, ETAT_EN_COURS
from src.indicateurs.types import EffectifTranche
from src.presentation.montant import (
    DEVISE,
    formater_montant,
    formater_nombre,
    libelle_devise,
)

LIBELLES_ETATS: dict[str, str] = {
    ETAT_EN_COURS: "Conversation en cours",
    ETAT_COMPLETE: "Estimation envoyée",
    ETAT_ABANDONNEE: "Abandonnée",
}

# Le libellé porte l'information, la couleur ne fait que la renforcer : un
# tableau ne doit pas devenir illisible pour qui distingue mal les teintes.
VARIANTES_ETATS: dict[str, str] = {
    ETAT_EN_COURS: "bleu",
    ETAT_COMPLETE: "vert",
    ETAT_ABANDONNEE: "gris",
}

VARIANTES_CATEGORIES: dict[str, str] = {
    "salle": "bleu",
    "mobilier": "sarcelle",
    "restauration": "orange",
    "decoration": "violet",
    "sonorisation": "ambre",
    "personnel": "vert",
    "logistique": "gris",
}

HAUTEUR_BARRE_MINIMALE = 4


def titre_ecran(titre: str, sous_titre: str) -> str:
    """Titre et sous-titre d'un écran"""
    return (
        f'<div><h1 class="titre-ecran">{escape(titre)}</h1>'
        f'<div class="titre-ecran__sous">{escape(sous_titre)}</div></div>'
    )


def carte_indicateur(libelle: str, valeur: str, legende: str, unite: str | None = None) -> str:
    """Carte d'un indicateur : son libellé, son chiffre, sa devise et sa légende"""
    suffixe = f'<span class="carte__unite">{escape(unite)}</span>' if unite else ""
    return _carte(
        libelle,
        f'<div class="carte__valeur">{escape(valeur)}{suffixe}</div>'
        f'<div class="carte__legende">{escape(legende)}</div>',
    )


def carte_montant(libelle: str, montant: int, legende: str) -> str:
    """Carte d'un montant en FCFA, devise séparée du nombre pour rester lisible"""
    return carte_indicateur(libelle, formater_nombre(montant), legende, unite=DEVISE)


def carte_tranches(libelle: str, effectifs: list[EffectifTranche], legende: str) -> str:
    """Répartition par tranche d'invités, en barres proportionnelles.

    Tout à zéro donne un message explicite plutôt que quatre barres plates :
    un graphique vide se lit comme une panne.
    """
    maximum = max((effectif.nombre_demandes for effectif in effectifs), default=0)
    if maximum == 0:
        return _carte(
            libelle, f'<div class="carte__legende">{escape("Aucune demande sur la période.")}</div>'
        )

    barres = "".join(
        f'<div class="tranche">'
        f'<span class="tranche__effectif">{effectif.nombre_demandes}</span>'
        f'<div class="tranche__barre{_classe_barre(effectif.nombre_demandes)}" '
        f'style="height:{_hauteur_barre(effectif.nombre_demandes, maximum)}%"></div>'
        f'<span class="tranche__libelle">{escape(effectif.tranche)}</span>'
        f"</div>"
        for effectif in effectifs
    )
    return _carte(
        libelle,
        f'<div class="tranches">{barres}</div>'
        f'<div class="carte__legende">{escape(legende)}</div>',
    )


def bande_indicateur(valeur: str, libelle: str) -> str:
    """Indicateur secondaire, sur une seule ligne discrète"""
    return (
        f'<div class="bande"><span class="bande__valeur">{escape(valeur)}</span>'
        f'<span class="bande__libelle">{escape(libelle)}</span></div>'
    )


def pastille(texte: str, variante: str) -> str:
    """Pastille colorée dont le libellé suffit à comprendre, sans la couleur"""
    return f'<span class="pastille pastille--{escape(variante)}">{escape(texte)}</span>'


def pastille_etat(etat: str) -> str:
    """Pastille de l'état d'une demande"""
    return pastille(LIBELLES_ETATS.get(etat, etat), VARIANTES_ETATS.get(etat, "gris"))


def pastille_categorie(categorie: str) -> str:
    """Pastille de la catégorie d'une ressource du catalogue"""
    return pastille(
        libelle_categorie(categorie).capitalize(), VARIANTES_CATEGORIES.get(categorie, "gris")
    )


def cellule_montant(montant: int | None, devise: str | None) -> str:
    """Montant aligné à droite avec sa devise en retrait, ou un tiret s'il n'y en a pas.

    Une demande sans devis n'a pas de montant : un tiret le dit, là où un zéro
    laisserait croire à une estimation gratuite.
    """
    if montant is None:
        return '<span class="table__secondaire">—</span>'
    return (
        f"{escape(formater_nombre(montant))}"
        f'<span class="table__devise">{escape(libelle_devise(devise))}</span>'
    )


def cellule_double(principal: str, secondaire: str | None = None) -> str:
    """Cellule à deux niveaux : la valeur qui compte, puis une précision"""
    ligne_secondaire = (
        f'<div class="table__secondaire">{escape(secondaire)}</div>' if secondaire else ""
    )
    return f'<div class="table__principal">{escape(principal)}</div>{ligne_secondaire}'


def tableau(entetes: list[tuple[str, str]], lignes: list[list[str]]) -> str:
    """Tableau HTML défilant. Les cellules reçues sont du HTML déjà échappé.

    Les en-têtes viennent en couples (libellé, classe), et la classe s'applique
    aussi aux cellules de la colonne : une colonne de montants s'aligne ainsi à
    droite d'un seul réglage, en-tête et contenu ensemble. Poser la classe sur
    un span à l'intérieur de la cellule ne l'alignerait pas, un span étant en
    ligne.
    """
    classes = [classe for _, classe in entetes]
    colonnes = "".join(
        f'<th class="{escape(classe)}">{escape(libelle)}</th>' for libelle, classe in entetes
    )
    corps = "".join(
        "<tr>"
        + "".join(
            f'<td class="{escape(classes[rang]) if rang < len(classes) else ""}">{cellule}</td>'
            for rang, cellule in enumerate(ligne)
        )
        + "</tr>"
        for ligne in lignes
    )
    return (
        f'<div class="defilement"><table class="table">'
        f"<thead><tr>{colonnes}</tr></thead><tbody>{corps}</tbody></table></div>"
    )


def panneau(titre: str, compte: str, contenu: str) -> str:
    """Panneau blanc à en-tête, autour d'un tableau déjà construit"""
    return (
        f'<div class="panneau-liste"><div class="panneau-liste__entete">'
        f'<span class="panneau-liste__titre">{escape(titre)}</span>'
        f'<span class="panneau-liste__compte">{escape(compte)}</span>'
        f"</div>{contenu}</div>"
    )


def etat_vide(titre: str, texte: str, code: str | None = None) -> str:
    """Écran vide expliqué : un tableau vide sans un mot se lit comme une panne"""
    repere = f'<div class="vide__code">{escape(code)}</div>' if code else ""
    return (
        f'<div class="vide"><div class="vide__titre">{escape(titre)}</div>'
        f'<div class="vide__texte">{escape(texte)}</div>{repere}</div>'
    )


def recapitulatif(titre: str, champs: list[tuple[str, str | None]]) -> str:
    """Bloc clé/valeur, de la même forme que le chat et le PDF.

    Une valeur absente se lit « — », le même tiret qu'ailleurs dans l'écran
    pour un montant sans devis (voir cellule_montant) : le besoin d'une
    conversation interrompue est incomplet par nature, sans qu'il faille le
    dire en toutes lettres à chaque champ.
    """
    lignes = "".join(
        f'<div class="recap__ligne"><span class="recap__cle">{escape(cle)}</span>'
        + (
            f'<span class="recap__valeur">{escape(valeur)}</span>'
            if valeur
            else '<span class="recap__valeur recap__valeur--manquant">—</span>'
        )
        + "</div>"
        for cle, valeur in champs
    )
    return (
        f'<div class="recap"><div class="recap__titre">{escape(titre)}</div>{lignes}</div>'
    )


def tableau_devis(devis: DevisConsulte) -> str:
    """Lignes figées d'un devis émis et son total, jamais recalculés (D11)"""
    lignes = [
        [
            escape(ligne.designation),
            escape(formater_nombre(ligne.quantite)),
            escape(formater_montant(ligne.prix_unitaire)),
            escape(formater_montant(ligne.montant)),
        ]
        for ligne in devis.lignes
    ]
    corps = tableau(
        [
            ("Prestation", ""),
            ("Quantité", "table__nb"),
            ("Prix unitaire", "table__nb"),
            ("Montant", "table__nb"),
        ],
        lignes,
    )
    return (
        f'<div class="panneau-liste">{corps}'
        f'<div class="total"><span class="total__libelle">Total estimé</span>'
        f'<span class="total__montant">{escape(formater_montant(devis.total))}</span></div></div>'
    )


def resume_evenement(demande: LigneListeDemande) -> str:
    """Une ligne de contexte : invités, ville et quartier tels qu'extraits"""
    morceaux = []
    if demande.nombre_invites is not None:
        morceaux.append(f"{formater_nombre(demande.nombre_invites)} invités")
    if demande.ville:
        morceaux.append(demande.ville)
    if demande.quartier_souhaite:
        morceaux.append(demande.quartier_souhaite)
    return " · ".join(morceaux)


def date_francaise(date_iso: str | None) -> str | None:
    """Date ISO écrite à la française, telle quelle si elle n'est pas une date.

    Le besoin garde la date que l'extraction a produite : « mi-décembre » y
    reste tel quel, et doit s'afficher tel quel plutôt que disparaître.
    """
    if not date_iso:
        return None
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return date_iso


def accorder(nombre: int, singulier: str, pluriel: str | None = None) -> str:
    """Nombre suivi du mot accordé : « 1 demande », « 8 demandes »"""
    mot = singulier if abs(nombre) <= 1 else (pluriel or f"{singulier}s")
    return f"{formater_nombre(nombre)} {mot}"


def _carte(libelle: str, contenu: str) -> str:
    """Coquille commune des cartes d'indicateurs"""
    return (
        f'<div class="carte"><div class="carte__libelle">{escape(libelle)}</div>{contenu}</div>'
    )


def _classe_barre(effectif: int) -> str:
    """Une tranche sans demande garde une barre grise, visible mais neutre"""
    return "" if effectif else " tranche__barre--vide"


def _hauteur_barre(effectif: int, maximum: int) -> int:
    """Hauteur en pourcentage, proportionnelle à la tranche la plus fournie"""
    if effectif == 0:
        return HAUTEUR_BARRE_MINIMALE
    return max(HAUTEUR_BARRE_MINIMALE, round(100 * effectif / maximum))
