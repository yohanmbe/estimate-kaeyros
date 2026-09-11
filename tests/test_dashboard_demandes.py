"""Écran des demandes reçues : liste filtrable et détail en lecture seule.

Le détail doit porter tout ce qu'il faut au commercial pour rappeler un
prospect (D26) et les lignes du devis telles qu'elles ont été émises (D11).
"""
from datetime import datetime

from src.presentation.montant import formater_montant
from tests.aide_dashboard import (
    BESOIN_MARIAGE_250,
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


def test_periode_tout_montre_les_demandes_de_toutes_les_periodes(base_branchee):
    """« Tout » (voir D48) ne doit borner par aucune date : une demande de
    2021 doit y apparaître alors qu'elle sort de « Cette année » (2026).
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee, tenant, datetime(2021, 3, 1), nom_prospect="Ancienne demande"
    )

    ecran = ouvrir_ecran(tenant.id)
    assert "Ancienne demande" not in texte_affiche(ecran)

    ecran = ecran.segmented_control[1].set_value("Tout").run()

    assert "Ancienne demande" in texte_affiche(ecran)


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
    assert "Relance autorisée" in texte
    # La date du besoin est stockee en ISO et affichee a la francaise
    assert "12/12/2026" in texte


def test_detail_dun_prospect_a_sa_premiere_demande_affiche_premiere_demande(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER)
    ecran = ouvrir_ecran(tenant.id)

    texte = texte_affiche(cliquer(ecran, f"ouvrir-{demande.id}"))

    assert "Première demande" in texte


def test_detail_dun_prospect_revenu_affiche_le_nombre_de_demandes(base_branchee):
    """Même téléphone (voir D47), deux demandes : le détail de l'une doit
    signaler que ce prospect est déjà revenu."""
    tenant = installer_tenant(base_branchee)
    premiere = creer_demande(base_branchee, tenant, LE_15_JANVIER, telephone="699001122")
    seconde = creer_demande(base_branchee, tenant, LE_20_JANVIER, prospect=premiere.prospect)
    ecran = ouvrir_ecran(tenant.id)

    texte = texte_affiche(cliquer(ecran, f"ouvrir-{seconde.id}"))

    assert "2 demandes au total" in texte
    assert "Première demande" not in texte


def test_lhistorique_du_prospect_napparait_pas_dans_la_liste(base_branchee):
    """« Première demande » / « N demandes au total » n'a de sens que sur le
    détail d'une demande : la liste ne doit pas l'afficher."""
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, LE_15_JANVIER)

    texte = texte_affiche(ouvrir_ecran(tenant.id))

    assert "Première demande" not in texte
    assert "au total" not in texte


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


def test_detail_affiche_les_mots_du_prospect(base_branchee):
    """C'est ce que le commercial lit en premier pour rappeler quelqu'un"""
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee,
        tenant,
        LE_15_JANVIER,
        besoins_hors_catalogue="Un feu d'artifice de clôture",
        commentaire="Merci de me rappeler le matin",
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "Besoins hors catalogue" in texte
    assert "Un feu d'artifice de clôture" in texte
    assert "Mot du prospect" in texte
    assert "Merci de me rappeler le matin" in texte


def test_demande_sans_mot_du_prospect_naffiche_aucune_section_vide(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER)
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "Besoins hors catalogue" not in texte
    assert "Mot du prospect" not in texte


def test_mot_du_prospect_dune_autre_entreprise_reste_invisible(base_branchee):
    """Même filtrage que le reste du détail : le tenant_id, jamais l'identifiant seul"""
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    demande_fanta = creer_demande(
        base_branchee, fanta, LE_15_JANVIER, commentaire="Budget confidentiel de Fanta"
    )

    ecran = lancer_ecran_connecte(etoile.id, ecran="demandes")
    ecran.session_state["demande_ouverte"] = demande_fanta.id
    ecran = ecran.run()

    assert "Budget confidentiel de Fanta" not in texte_affiche(ecran)


def test_detail_affiche_les_prestations_demandees_sur_mesure(base_branchee):
    """Une intention d'achat que le catalogue n'a pas servie : elle ne doit pas se perdre"""
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(
        base_branchee,
        tenant,
        LE_15_JANVIER,
        besoin={**BESOIN_MARIAGE_250, "categories_sur_mesure": ["salle", "decoration"]},
    )
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    texte = texte_affiche(ecran)
    assert "Proposition sur mesure attendue" in texte
    assert "Salle" in texte
    assert "Décoration" in texte


def test_demande_sans_sur_mesure_naffiche_pas_la_section(base_branchee):
    tenant = installer_tenant(base_branchee)
    demande = creer_demande(base_branchee, tenant, LE_15_JANVIER)
    ecran = ouvrir_ecran(tenant.id)

    ecran = cliquer(ecran, f"ouvrir-{demande.id}")

    assert "Proposition sur mesure attendue" not in texte_affiche(ecran)


def test_sur_mesure_dune_autre_entreprise_reste_invisible(base_branchee):
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    demande_fanta = creer_demande(
        base_branchee,
        fanta,
        LE_15_JANVIER,
        besoin={**BESOIN_MARIAGE_250, "categories_sur_mesure": ["sonorisation"]},
    )

    ecran = lancer_ecran_connecte(etoile.id, ecran="demandes")
    ecran.session_state["demande_ouverte"] = demande_fanta.id
    ecran = ecran.run()

    assert "Proposition sur mesure attendue" not in texte_affiche(ecran)
