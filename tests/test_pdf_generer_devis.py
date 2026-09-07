"""Le PDF met en forme un devis déjà chiffré, sans jamais recalculer un montant"""
import base64
import re
import zlib

from src.canaux.types import TenantContexte
from src.extraction.types import Besoin
from src.moteur.types import CategorieNonSatisfaite, LigneDevis, ResultatChiffrage
from src.pdf.generer_devis import generer_pdf_devis

# Le plus petit PNG valide possible (1x1 pixel), pour tester l'insertion du
# logo sans dépendre d'une bibliothèque d'image dans les tests.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

TENANT = TenantContexte(id="t1", nom="Événements Étoile", slug="etoile", logo=None)
BESOIN_MARIAGE_300 = Besoin(
    type_evenement="mariage",
    date_evenement="2026-12-12",
    ville="Yaoundé",
    quartier_souhaite="Bastos",
    nombre_invites=300,
    duree_jours=1,
)


def resultat_mariage_300() -> ResultatChiffrage:
    return ResultatChiffrage(
        lignes=[
            LigneDevis(
                designation="Salle Étoile Bastos",
                quantite=1,
                prix_unitaire=450_000,
                montant=450_000,
                ressource_id="salle-1",
            ),
            LigneDevis(
                designation="Menu Standard",
                quantite=300,
                prix_unitaire=8_000,
                montant=2_400_000,
                ressource_id="menu-1",
            ),
        ],
        total=2_850_000,
        categories_non_satisfaites=[],
        depasse_budget=False,
    )


def texte_du_pdf(pdf_bytes: bytes) -> str:
    """Décompresse les flux du PDF pour retrouver le texte réellement dessiné"""
    morceaux = [
        zlib.decompress(brut)
        for brut in re.findall(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL)
        if _est_compresse(brut)
    ]
    return b"".join(morceaux).decode("latin-1", errors="replace")


def _est_compresse(brut: bytes) -> bool:
    try:
        zlib.decompress(brut)
        return True
    except zlib.error:
        return False


def test_pdf_commence_par_len_tete_dun_document_pdf_valide():
    pdf_bytes = generer_pdf_devis(resultat_mariage_300(), TENANT, BESOIN_MARIAGE_300)

    assert pdf_bytes.startswith(b"%PDF-")


def test_entete_porte_le_nom_du_tenant_jamais_celui_du_produit():
    pdf_bytes = generer_pdf_devis(resultat_mariage_300(), TENANT, BESOIN_MARIAGE_300)

    texte = texte_du_pdf(pdf_bytes)
    assert "toile" in texte  # partie non accentuée de « Étoile », stable selon l'encodage
    assert "Estimate" not in texte


def test_lignes_et_total_du_resultat_apparaissent_sans_etre_recalcules():
    resultat = resultat_mariage_300()

    texte = texte_du_pdf(generer_pdf_devis(resultat, TENANT, BESOIN_MARIAGE_300))

    assert "Menu Standard" in texte
    assert "2 850 000 FCFA" in texte


def test_mention_non_contractuelle_toujours_presente():
    texte = texte_du_pdf(
        generer_pdf_devis(resultat_mariage_300(), TENANT, BESOIN_MARIAGE_300)
    )

    assert "non contractuelle" in texte


def test_categorie_non_satisfaite_est_signalee_sans_etre_cachee():
    resultat = ResultatChiffrage(
        lignes=[],
        total=0,
        categories_non_satisfaites=[CategorieNonSatisfaite(categorie="salle")],
        depasse_budget=None,
    )

    texte = texte_du_pdf(generer_pdf_devis(resultat, TENANT, BESOIN_MARIAGE_300))

    assert "salle" in texte


def test_tenant_sans_logo_ne_fait_pas_echouer_la_generation():
    pdf_bytes = generer_pdf_devis(resultat_mariage_300(), TENANT, BESOIN_MARIAGE_300)

    assert pdf_bytes.startswith(b"%PDF-")


def test_tenant_avec_logo_integre_limage_dans_len_tete(tmp_path):
    chemin_logo = tmp_path / "logo.png"
    chemin_logo.write_bytes(PNG_1X1)
    tenant_avec_logo = TenantContexte(
        id="t1", nom="Événements Étoile", slug="etoile", logo=str(chemin_logo)
    )

    pdf_bytes = generer_pdf_devis(resultat_mariage_300(), tenant_avec_logo, BESOIN_MARIAGE_300)

    assert pdf_bytes.startswith(b"%PDF-")
    assert b"/Image" in pdf_bytes


def test_type_ville_et_quartier_saffichent_avec_une_majuscule_meme_extraits_en_minuscules():
    besoin_en_minuscules = Besoin(
        type_evenement="mariage",
        date_evenement="2026-12-12",
        ville="yaoundé",
        quartier_souhaite="bastos",
        nombre_invites=300,
        duree_jours=1,
    )

    texte = texte_du_pdf(generer_pdf_devis(resultat_mariage_300(), TENANT, besoin_en_minuscules))

    assert "Mariage" in texte
    assert "astos" in texte  # partie non accentuée-sensible de « Bastos »
    assert "bastos" not in texte


def test_nombre_dinvites_eleve_separe_les_milliers_pour_la_lisibilite():
    besoin_grand_evenement = Besoin(
        type_evenement="mariage",
        date_evenement="2026-12-12",
        ville="Yaoundé",
        nombre_invites=1500,
        duree_jours=2,
    )

    texte = texte_du_pdf(generer_pdf_devis(resultat_mariage_300(), TENANT, besoin_grand_evenement))

    assert "1 500" in texte


def test_nom_de_tenant_tres_long_napparait_pas_tronque():
    """Régression : cell() à largeur fixe laissait un nom trop long déborder
    hors de la page plutôt que de passer à la ligne (voir D14 : c'est
    justement l'identité que ce document doit montrer correctement)."""
    tenant_nom_long = TenantContexte(
        id="t1",
        nom="Organisation Événementielle Prestige du Cameroun et d'Afrique Centrale",
        slug="prestige",
        logo=None,
    )

    pdf_bytes = generer_pdf_devis(resultat_mariage_300(), tenant_nom_long, BESOIN_MARIAGE_300)

    assert pdf_bytes.startswith(b"%PDF-")
    texte = texte_du_pdf(pdf_bytes)
    assert "Organisation" in texte
    assert "Afrique Centrale" in texte
