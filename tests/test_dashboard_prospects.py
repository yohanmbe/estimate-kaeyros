"""Écran des prospects : carnet d'adresses filtrable et fiche en lecture seule.

L'écran des demandes entre par la demande, celui-ci entre par la personne
(voir D49). La fiche doit porter de quoi rappeler quelqu'un (D26) et tout son
historique de demandes, chacune ouvrable sur son détail.

Les chiffres et les filtres eux-mêmes sont testés dans
tests/test_consultation_prospects.py : ici on vérifie qu'ils arrivent à
l'écran, que la navigation boucle, et qu'une absence se lit comme telle.
"""
from datetime import date, datetime

from src.presentation.montant import formater_montant, formater_nombre
from tests.aide_dashboard import (
    cliquer,
    creer_demande,
    creer_prospect,
    installer_tenant,
    lancer_ecran_connecte,
    texte_affiche,
)

AUJOURDHUI = date.today()
CE_MOIS = datetime(AUJOURDHUI.year, AUJOURDHUI.month, 15)
IL_Y_A_LONGTEMPS = datetime(2021, 3, 1)


def ouvrir_ecran(tenant_id: str):
    """L'écran des prospects, sur son défaut « Tout »"""
    return lancer_ecran_connecte(tenant_id, ecran="prospects")


def test_liste_montre_le_prospect_et_son_activite(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "Prospects" in texte
    assert "Sylvie Nkoa" in texte
    assert "699001122" in texte
    assert CE_MOIS.strftime("%d/%m/%Y") in texte


def test_liste_naffiche_ni_email_ni_relance(base_branchee):
    """L'email reste un détail réservé à la fiche ; la relance concerne une
    demande, pas la personne (voir D49) — ni l'un ni l'autre n'a sa place
    dans une colonne de la liste.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "sylvie@example.cm" not in texte
    assert "Relance" not in texte


def test_prospect_revenu_napparait_quune_fois_avec_ses_deux_demandes(base_branchee):
    """Même téléphone, deux demandes : une seule ligne au carnet (voir D47)"""
    tenant = installer_tenant(base_branchee)
    premiere = creer_demande(base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa")
    creer_demande(base_branchee, tenant, CE_MOIS, prospect=premiere.prospect)

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert texte.count("Sylvie Nkoa") == 1
    assert "1 prospect" in texte


def test_prospect_sans_aucune_demande_est_quand_meme_liste(base_branchee):
    """Il a laissé ses coordonnées : c'est quelqu'un à rappeler"""
    tenant = installer_tenant(base_branchee)
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Bea Kum", telephone="690112233")

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "Bea Kum" in texte


def test_recherche_par_nom_ne_garde_que_le_prospect_voulu(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Jean Etoundi", telephone="677445566")
    ecran = ouvrir_ecran(tenant.id)

    ecran = ecran.text_input[0].set_value("etoundi").run()

    texte = texte_affiche(ecran)
    assert "Jean Etoundi" in texte
    assert "Sylvie Nkoa" not in texte


def test_recherche_par_numero_avec_des_espaces_retrouve_le_prospect(base_branchee):
    """Le geste de base : le numéro lu sur l'écran d'appel, espaces compris"""
    tenant = installer_tenant(base_branchee)
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Jean Etoundi", telephone="677445566")
    ecran = ouvrir_ecran(tenant.id)

    ecran = ecran.text_input[0].set_value("699 00 11").run()

    texte = texte_affiche(ecran)
    assert "Sylvie Nkoa" in texte
    assert "Jean Etoundi" not in texte


def test_recherche_sans_resultat_le_dit_plutot_que_de_laisser_un_tableau_vide(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="Sylvie Nkoa")
    ecran = ouvrir_ecran(tenant.id)

    ecran = ecran.text_input[0].set_value("Mbarga").run()

    assert "Aucun prospect ne correspond" in texte_affiche(ecran)


def test_ecran_souvre_sur_tout_le_carnet_et_la_periode_le_restreint(base_branchee):
    """Le défaut est « Tout » (voir D48) : on vient chercher quelqu'un, pas
    un bilan de période.
    """
    tenant = installer_tenant(base_branchee)
    creer_prospect(
        base_branchee, tenant, IL_Y_A_LONGTEMPS, nom="Bea Kum", telephone="690112233"
    )

    ecran = ouvrir_ecran(tenant.id)
    assert "Bea Kum" in texte_affiche(ecran)

    ecran = ecran.segmented_control[0].set_value("Ce mois").run()

    assert "Bea Kum" not in texte_affiche(ecran)
    assert "Aucun prospect sur cette période" in texte_affiche(ecran)


def test_sans_aucun_prospect_lecran_explique_par_ou_ils_arrivent(base_branchee):
    tenant = installer_tenant(base_branchee)

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "Aucun prospect pour l'instant" in texte
    assert "?slug=etoile" in texte


def test_fiche_porte_les_coordonnees_et_les_demandes_du_prospect(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-prospect-{demande.prospect.id}")

    texte = texte_affiche(ecran)
    assert "Coordonnées" in texte
    assert "699001122" in texte
    assert "sylvie@example.cm" in texte
    assert "Demandes de ce prospect" in texte
    assert "Mariage" in texte
    assert formater_nombre(2_225_000) in texte


def test_fiche_naffiche_pas_la_relance(base_branchee):
    """La relance concerne une demande, pas la personne (voir D49) : elle se
    lit sur le détail de chaque demande, jamais sur cette fiche.
    """
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-prospect-{demande.prospect.id}")

    assert "Relance" not in texte_affiche(ecran)


def test_fiche_dun_prospect_sans_demande_pousse_a_le_rappeler(base_branchee):
    tenant = installer_tenant(base_branchee)
    prospect = creer_prospect(base_branchee, tenant, CE_MOIS, nom="Bea Kum")
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-prospect-{prospect.id}")

    texte = texte_affiche(ecran)
    assert "Aucune demande" in texte
    assert "rappeler" in texte
    assert formater_montant(0) not in texte


def test_ouvrir_une_demande_depuis_la_fiche_mene_a_son_detail(base_branchee):
    """Le trajet complet demandé : prospect → ses demandes → une demande.

    prospect_ouvert est dépilé au passage : sans ça, revenir sur Prospects
    rouvrirait la fiche au lieu de la liste.
    """
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )
    ecran = cliquer(ouvrir_ecran(tenant.id), f"ouvrir-prospect-{demande.prospect.id}")

    ecran = cliquer(ecran, f"ouvrir-demande-prospect-{demande.id}")

    assert ecran.session_state["ecran"] == "demandes"
    assert ecran.session_state["demande_ouverte"] == demande.id
    assert "prospect_ouvert" not in ecran.session_state
    assert "Total estimé" in texte_affiche(ecran)


def test_retour_ramene_a_la_liste_des_prospects(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa")
    ecran = cliquer(ouvrir_ecran(tenant.id), f"ouvrir-prospect-{demande.prospect.id}")

    ecran = cliquer(ecran, "retour-prospects")

    assert "prospect_ouvert" not in ecran.session_state
    assert "Les personnes qui ont demandé une estimation" in texte_affiche(ecran)


def test_prospect_dune_autre_entreprise_reste_introuvable(base_branchee):
    """Forcer l'identifiant en session ne doit rien ouvrir : il circule dans
    les clés de widgets.
    """
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    demande_fanta = creer_demande(
        base_branchee, fanta, CE_MOIS, nom_prospect="Roger Tchoumi", total_devis=9_999_999
    )

    ecran = lancer_ecran_connecte(etoile.id, ecran="prospects")
    ecran.session_state["prospect_ouvert"] = demande_fanta.prospect.id
    ecran = ecran.run()

    texte = texte_affiche(ecran)
    assert "Prospect introuvable" in texte
    assert "Roger Tchoumi" not in texte
    assert formater_nombre(9_999_999) not in texte


def test_prospect_dun_nom_contenant_du_balisage_est_echappe(base_branchee):
    """Un nom est une saisie libre venue d'Internet, rendue en
    unsafe_allow_html : le balisage brut est lu ici, sans unescape.
    """
    tenant = installer_tenant(base_branchee)
    creer_prospect(base_branchee, tenant, CE_MOIS, nom="<script>alert('x')</script>")

    ecran = ouvrir_ecran(tenant.id)

    balisage = "\n".join(element.value for element in ecran.markdown)
    assert "<script>alert" not in balisage
    assert "&lt;script&gt;" in balisage
