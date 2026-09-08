"""Écran des indicateurs : ce qu'il affiche vient des fonctions de src/indicateurs.

Les chiffres eux-mêmes sont testés dans tests/test_indicateurs_*.py. Ici on
vérifie qu'ils arrivent bien à l'écran, que la période choisie les change, et
qu'une absence de données se lit comme telle plutôt que comme une panne.
"""
from datetime import date, datetime

from src.presentation.montant import formater_montant, formater_nombre
from tests.aide_dashboard import (
    creer_demande,
    installer_tenant,
    lancer_ecran_connecte,
    texte_affiche,
)

AUJOURDHUI = date.today()
CE_MOIS = datetime(AUJOURDHUI.year, AUJOURDHUI.month, 15)


def un_mois_avant(reference: date) -> datetime:
    """Une date du mois précédent, hors du mois courant mais dans l'année"""
    if reference.month == 1:
        return datetime(reference.year, 1, 1)
    return datetime(reference.year, reference.month - 1, 15)


def test_les_trois_indicateurs_affiches_de_d19_sont_tous_presents(base_branchee):
    """Le montant moyen fait partie de D19 mais n'est plus affiché ici, à la
    demande du gestionnaire (voir D19) : seuls trois indicateurs restent en
    carte, le quatrième (répartition par tranche) portant sur une autre carte.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, total_devis=2_225_000)

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "Demandes reçues" in texte
    assert "Total estimé cumulé" in texte
    assert "Montant moyen" not in texte
    assert "Par nombre d'invités" in texte


def test_total_cumule_est_affiche_au_franc_pres(base_branchee):
    """Deux devis de 2 000 000 et 3 000 000 : total 5 000 000"""
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, total_devis=2_000_000)
    creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Jean Etoundi", total_devis=3_000_000
    )

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert formater_nombre(5_000_000) in texte


def test_repartition_par_tranche_montre_les_quatre_tranches(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, besoin={"nombre_invites": 60})
    creer_demande(
        base_branchee, tenant, CE_MOIS, besoin={"nombre_invites": 700}, nom_prospect="Bea Kum"
    )

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "< 100" in texte
    assert "100-250" in texte
    assert "251-500" in texte
    assert "500+" in texte


def test_les_deux_indicateurs_complementaires_sont_affiches(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, total_devis=2_225_000)

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "acceptent d'être recontactés" in texte
    assert "ont reçu une estimation" in texte


def test_aucun_indicateur_de_conversion_commerciale_nest_affiche(base_branchee):
    """D19 l'interdit : le produit s'arrête à l'estimation et ne sait pas ce
    qu'une demande devient ensuite.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, total_devis=2_225_000)

    texte = texte_affiche(lancer_ecran_connecte(tenant.id)).lower()

    assert "conversion" not in texte
    assert "chiffre d'affaires" not in texte
    assert "vente" not in texte


def test_periode_choisie_change_les_chiffres_affiches(base_branchee):
    """Une demande du mois dernier sort de « Ce mois » et revient sur l'année"""
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, un_mois_avant(AUJOURDHUI), total_devis=4_444_000)

    ecran = lancer_ecran_connecte(tenant.id)
    assert formater_nombre(4_444_000) not in texte_affiche(ecran)

    ecran = ecran.segmented_control[0].set_value("Cette année").run()

    assert formater_nombre(4_444_000) in texte_affiche(ecran)


def test_dernieres_demandes_montrent_le_prospect_et_son_total(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(
        base_branchee, tenant, CE_MOIS, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "Dernières demandes reçues" in texte
    assert "Sylvie Nkoa" in texte
    assert formater_nombre(2_225_000) in texte
    assert "Mariage" in texte


def test_seules_les_cinq_dernieres_demandes_sont_listees(base_branchee):
    tenant = installer_tenant(base_branchee)
    for jour in range(1, 8):
        creer_demande(
            base_branchee,
            tenant,
            datetime(AUJOURDHUI.year, AUJOURDHUI.month, jour),
            nom_prospect=f"Prospect {jour}",
        )

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "Prospect 7" in texte
    assert "Prospect 3" in texte
    assert "Prospect 2" not in texte
    assert "Prospect 1" not in texte


def test_demande_sans_devis_affiche_un_tiret_plutot_quun_zero(base_branchee):
    """Une conversation en cours n'a pas de montant : zéro laisserait croire à
    une estimation gratuite.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS)

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "Conversation en cours" in texte
    assert formater_montant(0) not in texte


def test_sans_aucune_demande_lecran_explique_par_ou_elles_arrivent(base_branchee):
    """Un tableau vide sans un mot se lit comme une panne"""
    tenant = installer_tenant(base_branchee)

    texte = texte_affiche(lancer_ecran_connecte(tenant.id))

    assert "Aucune demande sur cette période" in texte
    assert "?slug=etoile" in texte
    assert "Aucune demande sur la période." in texte


def test_lien_vers_la_liste_complete_mene_a_lecran_des_demandes(base_branchee):
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, CE_MOIS, total_devis=2_225_000)
    ecran = lancer_ecran_connecte(tenant.id)

    ecran = next(b for b in ecran.button if b.key == "voir-toutes-les-demandes").click().run()

    assert "Demandes reçues" in texte_affiche(ecran)
