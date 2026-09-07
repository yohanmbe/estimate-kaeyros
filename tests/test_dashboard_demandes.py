"""Écran des demandes reçues : liste filtrable et détail en lecture seule.

Le détail doit porter tout ce qu'il faut au commercial pour rappeler un
prospect (D26) et les lignes du devis telles qu'elles ont été émises (D11).
"""
from datetime import datetime

from src.presentation.montant import formater_montant
from tests.aide_dashboard import (
    cliquer,
    creer_demande,
    installer_tenant,
    lancer_ecran_connecte,
    texte_affiche,
)

LE_15_JANVIER = datetime(2026, 1, 15)
LE_20_JANVIER = datetime(2026, 1, 20)


def ouvrir_ecran(tenant_id: str):
    """L'écran des demandes, sur l'année pour ne dépendre d'aucune date du jour"""
    ecran = lancer_ecran_connecte(tenant_id, ecran="demandes")
    return ecran.segmented_control[1].set_value("Cette année").run()


def test_liste_montre_la_demande_son_prospect_et_son_total(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee, tenant, LE_15_JANVIER, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "Sylvie Nkoa" in texte
    assert "Mariage" in texte
    assert "250 invités" in texte.replace("\xa0", " ")
    assert "Bastos" in texte
    assert "Estimation envoyée" in texte


def test_filtre_de_statut_ne_garde_que_les_demandes_voulues(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, LE_15_JANVIER, nom_prospect="Sans estimation")
    creer_demande(
        base_branchee,
        tenant,
        LE_20_JANVIER,
        nom_prospect="Avec estimation",
        total_devis=2_225_000,
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = ecran.segmented_control[0].set_value("Estimation envoyée").run()

    texte = texte_affiche(ecran)
    assert "Avec estimation" in texte
    assert "Sans estimation" not in texte


def test_filtre_sans_resultat_le_dit_sans_laisser_un_tableau_vide(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, LE_15_JANVIER, nom_prospect="Sans estimation")
    ecran = ouvrir_ecran(tenant.id)

    ecran = ecran.segmented_control[0].set_value("Estimation envoyée").run()

    assert "Aucune demande avec ce statut" in texte_affiche(ecran)


def test_le_filtre_abandonnee_nest_pas_propose(base_branchee):
    """Rien dans le produit ne sait écrire cet état : un filtre qui ne peut
    jamais rien renvoyer vaudrait moins que pas de filtre.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, LE_15_JANVIER)

    ecran = ouvrir_ecran(tenant.id)

    assert "Abandonnée" not in texte_affiche(ecran)


def test_detail_dune_demande_porte_le_besoin_et_les_coordonnees(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee, tenant, LE_15_JANVIER, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "L'événement" in texte
    assert "Demandé par" in texte
    assert "699001122" in texte
    assert "sylvie@example.cm" in texte
    assert "Recontact accepté" in texte
    # La date du besoin est stockee en ISO et affichee a la francaise
    assert "12/12/2026" in texte


def test_detail_affiche_les_lignes_figees_du_devis_et_son_total(base_branchee):
    """Les lignes viennent de la base, elles ne sont jamais rechiffrées (D11)"""
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER, total_devis=2_225_000)
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "Salle des fêtes Le Bastos" in texte
    assert "Menu complet invité" in texte
    assert formater_montant(7_500) in texte
    assert formater_montant(1_875_000) in texte
    assert formater_montant(2_225_000) in texte
    assert "Total estimé" in texte


def test_detail_dune_demande_sans_devis_pousse_a_rappeler_le_prospect(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER)
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "Aucune estimation émise" in texte
    assert "rappeler ce prospect" in texte


def test_retour_ramene_a_la_liste(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER, total_devis=2_225_000)
    ecran = cliquer(ouvrir_ecran(tenant.id), f"ouvrir-{demande.id}")

    ecran = cliquer(ecran, "retour-demandes")

    assert "Demandes reçues" in texte_affiche(ecran)
    assert "demande_ouverte" not in ecran.session_state


def test_demande_dune_autre_entreprise_reste_introuvable(base_branchee):
    """L'identifiant d'une demande voyage dans les clés de widgets : le forcer
    en session ne doit rien ouvrir.
    """
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    demande_fanta = creer_demande(
        base_branchee, fanta, LE_15_JANVIER, nom_prospect="Roger Tchoumi", total_devis=9_999_999
    )

    ecran = lancer_ecran_connecte(etoile.id, ecran="demandes")
    ecran.session_state["demande_ouverte"] = demande_fanta.id
    ecran = ecran.run()

    texte = texte_affiche(ecran)
    assert "Demande introuvable" in texte
    assert "Roger Tchoumi" not in texte
    assert formater_montant(9_999_999) not in texte


def test_prospect_dun_nom_contenant_du_balisage_est_echappe(base_branchee):
    """Le nom vient d'une saisie libre sur Internet et la page est rendue en
    unsafe_allow_html : sans échappement, ce serait une injection de script
    dans l'écran du gestionnaire.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee,
        tenant,
        LE_15_JANVIER,
        nom_prospect="<script>alert('x')</script>",
    )

    ecran = ouvrir_ecran(tenant.id)

    balisage = "\n".join(element.value for element in ecran.markdown)
    assert "<script>alert" not in balisage
    assert "&lt;script&gt;" in balisage
