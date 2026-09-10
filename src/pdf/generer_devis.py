"""Mise en forme PDF d'un devis déjà chiffré (voir D14).

Ce module ne calcule aucun montant : il reçoit un ResultatChiffrage déjà
produit par src/moteur et se contente de le présenter. L'en-tête porte le
nom et le logo du tenant, jamais ceux du produit (D14) : le prospect
achète à l'entreprise événementielle, pas à Estimate.
"""
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos

from src.canaux.types import TenantContexte
from src.catalogue.vocabulaire import libelle_categorie
from src.extraction.types import Besoin
from src.moteur.types import LigneDevis, ResultatChiffrage
from src.presentation.montant import formater_montant, formater_nombre

MENTION_NON_CONTRACTUELLE = "Estimation indicative, non contractuelle"

HAUTEUR_LOGO_MM = 18
ESPACE_APRES_LOGO_MM = 6
# Au-delà, un logo au format très large empièterait sur le nom du tenant :
# mieux vaut le laisser déborder un peu que rendre l'en-tête illisible.
LARGEUR_MAX_RESERVEE_LOGO_MM = 70

# Palette reprise de la barre latérale du chat (voir FEUILLE_DE_STYLE dans
# streamlit_prospect.py), pour que le PDF prolonge ce que le prospect a déjà
# vu à l'écran plutôt que de retomber dans un simple noir et blanc administratif.
COULEUR_TITRE_SECTION = (217, 79, 0)  # --orange-texte
COULEUR_CLE = (91, 97, 120)  # --gris
COULEUR_VALEUR = (10, 31, 111)  # --bleu-fonce
COULEUR_VALEUR_MANQUANTE = (182, 188, 205)  # --recap__valeur--manquant
COULEUR_FILET = (226, 230, 242)  # --trait
COULEUR_BORDURE_TABLE = (210, 216, 236)
COULEUR_FOND_ENTETE_TABLE = (234, 238, 251)  # --bleu-pale
COULEUR_FOND_ZEBRA = (251, 251, 254)
COULEUR_FOND_TOTAL = (221, 228, 249)  # --bleu-pale-vif
COULEUR_FOND_ALERTE = (255, 241, 230)  # --orange-pale
COULEUR_TEXTE_ALERTE = (125, 60, 0)
COULEUR_FOND_MENTION = (244, 245, 251)  # --fond


def generer_pdf_devis(
    resultat: ResultatChiffrage,
    tenant: TenantContexte,
    besoin: Besoin,
) -> bytes:
    """Met en forme un devis déjà chiffré en PDF, prêt à être téléchargé"""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    _dessiner_entete(pdf, tenant)
    _dessiner_recapitulatif_besoin(pdf, besoin)
    _dessiner_tableau_lignes(pdf, resultat.lignes)
    _dessiner_total(pdf, resultat.total)
    if resultat.categories_non_satisfaites:
        _dessiner_categories_non_chiffrees(pdf, resultat, besoin)
    _dessiner_mention(pdf, tenant)

    return bytes(pdf.output())


def _dessiner_entete(pdf: FPDF, tenant: TenantContexte) -> None:
    """En-tête au nom, au logo et aux coordonnées du tenant, jamais ceux du produit (D14)"""
    x_texte = pdf.l_margin
    if tenant.logo and Path(tenant.logo).is_file():
        image = pdf.image(tenant.logo, x=pdf.l_margin, y=pdf.t_margin, h=HAUTEUR_LOGO_MM)
        x_texte = min(
            pdf.l_margin + image.rendered_width + ESPACE_APRES_LOGO_MM,
            pdf.l_margin + LARGEUR_MAX_RESERVEE_LOGO_MM,
        )

    pdf.set_xy(x_texte, pdf.t_margin)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*COULEUR_VALEUR)
    # multi_cell, jamais cell() à largeur fixe : un nom de tenant trop long
    # pour tenir sur une ligne doit passer à la ligne, pas déborder hors page.
    pdf.multi_cell(pdf.epw - (x_texte - pdf.l_margin), 8, tenant.nom, new_x=XPos.LEFT, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COULEUR_CLE)
    if tenant.coordonnees:
        pdf.cell(0, 6, tenant.coordonnees, new_x=XPos.LEFT, new_y=YPos.NEXT)
    pdf.cell(
        0, 6,
        f"Estimation établie le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        new_x=XPos.LEFT, new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)

    pdf.set_y(max(pdf.get_y(), pdf.t_margin + HAUTEUR_LOGO_MM))
    pdf.set_x(pdf.l_margin)
    pdf.ln(3)
    _tracer_ligne_pleine(pdf, COULEUR_FILET)
    pdf.ln(5)


HAUTEUR_LIGNE_RECAP_MM = 7


def _dessiner_recapitulatif_besoin(pdf: FPDF, besoin: Besoin) -> None:
    """Rappelle l'événement décrit par le prospect, tel qu'extrait"""
    champs = [
        ("Type", _mettre_en_forme(besoin.type_evenement)),
        ("Date", besoin.date_evenement),
        ("Ville", _mettre_en_forme(besoin.ville)),
        ("Quartier", _mettre_en_forme(besoin.quartier_souhaite)),
        ("Invités", formater_nombre(besoin.nombre_invites) if besoin.nombre_invites else None),
        ("Durée", f"{besoin.duree_jours} jour(s)" if besoin.duree_jours else None),
    ]
    _dessiner_section_cle_valeur(pdf, "VOTRE ÉVÉNEMENT", champs)


def _dessiner_section_cle_valeur(
    pdf: FPDF, titre: str, champs: list[tuple[str, str | None]]
) -> None:
    """Bloc de lignes clé/valeur teinté, séparées d'un filet pointillé — même
    forme et mêmes couleurs que le récapitulatif de la barre latérale du chat
    (voir streamlit_prospect.py). Une valeur absente se lit « à préciser » ;
    pour un champ facultatif qui n'a simplement rien à afficher (l'email du
    prospect, par exemple), ne pas inclure la ligne plutôt que de la passer.
    """
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_char_spacing(0.5)
    pdf.set_text_color(*COULEUR_TITRE_SECTION)
    pdf.cell(0, 6, titre, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_char_spacing(0)

    largeur_cle = pdf.epw * 0.35
    largeur_valeur = pdf.epw * 0.65
    for cle, valeur in champs:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*COULEUR_CLE)
        pdf.cell(largeur_cle, HAUTEUR_LIGNE_RECAP_MM, cle)

        pdf.set_font("Helvetica", "" if valeur is None else "B", 10)
        pdf.set_text_color(*(COULEUR_VALEUR_MANQUANTE if valeur is None else COULEUR_VALEUR))
        pdf.cell(
            largeur_valeur, HAUTEUR_LIGNE_RECAP_MM, valeur or "à préciser", align="R",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        _tracer_filet_pointille(pdf)

    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def _mettre_en_forme(valeur: str | None) -> str | None:
    """Première lettre de chaque mot en majuscule, pour l'affichage seulement.

    Le besoin garde sa valeur d'origine (« mariage », « yaoundé »...) telle
    qu'extraite : cette fonction ne change que ce qui est imprimé.
    """
    return valeur.strip().title() if valeur else None


def _tracer_filet_pointille(pdf: FPDF) -> None:
    """Sépare deux lignes du récapitulatif, comme le filet pointillé du chat"""
    y = pdf.get_y()
    pdf.set_dash_pattern(dash=1, gap=1)
    _tracer_ligne_pleine(pdf, COULEUR_FILET, y)
    pdf.set_dash_pattern()


def _tracer_ligne_pleine(pdf: FPDF, couleur: tuple[int, int, int], y: float | None = None) -> None:
    """Ligne horizontale sur toute la largeur du contenu"""
    y = pdf.get_y() if y is None else y
    pdf.set_draw_color(*couleur)
    pdf.line(pdf.l_margin, y, pdf.l_margin + pdf.epw, y)
    pdf.set_draw_color(0, 0, 0)


def _dessiner_tableau_lignes(pdf: FPDF, lignes: list[LigneDevis]) -> None:
    """Une ligne du tableau par ligne du devis, montants déjà calculés"""
    largeur_designation = pdf.epw * 0.40
    largeur_quantite = pdf.epw * 0.15
    largeur_prix = pdf.epw * 0.20
    largeur_montant = pdf.epw * 0.25
    hauteur_ligne = 8

    pdf.set_draw_color(*COULEUR_BORDURE_TABLE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*COULEUR_FOND_ENTETE_TABLE)
    pdf.set_text_color(*COULEUR_VALEUR)
    pdf.cell(largeur_designation, hauteur_ligne, "Prestation", border=1, fill=True)
    pdf.cell(largeur_quantite, hauteur_ligne, "Quantité", border=1, fill=True, align="R")
    pdf.cell(largeur_prix, hauteur_ligne, "Prix unitaire", border=1, fill=True, align="R")
    pdf.cell(
        largeur_montant, hauteur_ligne, "Montant", border=1, fill=True, align="R",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 40)
    for rang, ligne in enumerate(lignes):
        pdf.set_fill_color(*(COULEUR_FOND_ZEBRA if rang % 2 else (255, 255, 255)))
        pdf.cell(largeur_designation, hauteur_ligne, ligne.designation, border=1, fill=True)
        pdf.cell(largeur_quantite, hauteur_ligne, str(ligne.quantite), border=1, fill=True, align="R")
        pdf.cell(
            largeur_prix, hauteur_ligne, formater_montant(ligne.prix_unitaire),
            border=1, fill=True, align="R",
        )
        pdf.cell(
            largeur_montant, hauteur_ligne, formater_montant(ligne.montant), border=1, fill=True,
            align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)


HAUTEUR_BANDEAU_TOTAL_MM = 16
MARGE_INTERIEURE_BANDEAU_MM = 5


def _dessiner_total(pdf: FPDF, total: int) -> None:
    """Le total du devis, mis en évidence dans un bandeau : c'est le seul
    chiffre que le prospect doit repérer en un coup d'œil.
    """
    pdf.ln(4)
    y = pdf.get_y()
    pdf.set_fill_color(*COULEUR_FOND_TOTAL)
    pdf.rect(
        pdf.l_margin, y, pdf.epw, HAUTEUR_BANDEAU_TOTAL_MM,
        style="F", round_corners=True, corner_radius=2,
    )

    largeur_interieure = pdf.epw - 2 * MARGE_INTERIEURE_BANDEAU_MM
    pdf.set_xy(pdf.l_margin + MARGE_INTERIEURE_BANDEAU_MM, y + 4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COULEUR_VALEUR)
    pdf.cell(largeur_interieure * 0.45, 8, "Total estimé")

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*COULEUR_TITRE_SECTION)
    pdf.cell(largeur_interieure * 0.55, 8, formater_montant(total), align="R")
    pdf.set_text_color(0, 0, 0)

    pdf.set_xy(pdf.l_margin, y + HAUTEUR_BANDEAU_TOTAL_MM)


def _dessiner_categories_non_chiffrees(
    pdf: FPDF, resultat: ResultatChiffrage, besoin: Besoin
) -> None:
    """Signale ce qui n'est pas chiffré, en distinguant ce que le prospect a demandé.

    Ranger une prestation demandée sur mesure sous « hors catalogue »
    reviendrait à lui répondre que ce qu'il vient de réclamer n'existe pas.
    """
    sur_mesure = [
        categorie.categorie
        for categorie in resultat.categories_non_satisfaites
        if categorie.categorie in besoin.categories_sur_mesure
    ]
    autres = [
        categorie.categorie
        for categorie in resultat.categories_non_satisfaites
        if categorie.categorie not in besoin.categories_sur_mesure
    ]

    if sur_mesure:
        pdf.ln(4)
        _dessiner_encart(
            pdf,
            f"Proposition sur mesure à venir : {_enumerer_categories(sur_mesure)}. "
            "Un commercial vous communiquera le prix.",
            COULEUR_FOND_ALERTE, COULEUR_TEXTE_ALERTE,
        )
    if autres:
        pdf.ln(4)
        _dessiner_encart(
            pdf, f"Non chiffré, hors catalogue actuel : {_enumerer_categories(autres)}.",
            COULEUR_FOND_ALERTE, COULEUR_TEXTE_ALERTE,
        )


def _enumerer_categories(categories: list[str]) -> str:
    """Liste de catégories dans leur libellé lisible"""
    return ", ".join(libelle_categorie(categorie) for categorie in categories)


def _dessiner_mention(pdf: FPDF, tenant: TenantContexte) -> None:
    """Mention obligatoire : une estimation n'engage pas l'entreprise (D12).
    Placée dans un encart pour rester visible même en bas de page, jamais
    réduite à une ligne de petits caractères qu'on oublie de lire.
    """
    pdf.ln(4)
    _dessiner_encart(
        pdf,
        f"{MENTION_NON_CONTRACTUELLE}, établie à partir du catalogue de {tenant.nom}.",
        COULEUR_FOND_MENTION, COULEUR_CLE,
    )


MARGE_INTERIEURE_ENCART_MM = 4


def _dessiner_encart(
    pdf: FPDF, texte: str, couleur_fond: tuple[int, int, int], couleur_texte: tuple[int, int, int]
) -> None:
    """Encart arrondi et teinté pour une information qui ne doit pas passer
    inaperçue, plutôt qu'une ligne de texte perdue dans le reste du document.
    """
    largeur_interieure = pdf.epw - 2 * MARGE_INTERIEURE_ENCART_MM
    pdf.set_font("Helvetica", "I", 9)
    hauteur_texte = pdf.multi_cell(
        largeur_interieure, 5, texte, dry_run=True, output=MethodReturnValue.HEIGHT
    )
    hauteur_encart = hauteur_texte + 2 * MARGE_INTERIEURE_ENCART_MM

    y = pdf.get_y()
    pdf.set_fill_color(*couleur_fond)
    pdf.rect(pdf.l_margin, y, pdf.epw, hauteur_encart, style="F", round_corners=True, corner_radius=2)

    pdf.set_xy(pdf.l_margin + MARGE_INTERIEURE_ENCART_MM, y + MARGE_INTERIEURE_ENCART_MM)
    pdf.set_text_color(*couleur_texte)
    pdf.multi_cell(largeur_interieure, 5, texte)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(pdf.l_margin, y + hauteur_encart)
