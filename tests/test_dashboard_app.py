"""Garde de la porte, navigation, et cloisonnement au niveau de l'écran.

Le tenant_id ne vient que de la session établie à la connexion. Les tests
d'isolation portent donc sur ce que l'écran rend : un second tenant peuplé ne
doit apparaître nulle part, et un paramètre d'URL ne doit rien y changer.
"""
from datetime import datetime

from streamlit.testing.v1 import AppTest

from src.presentation.montant import formater_montant, formater_nombre

from tests.aide_dashboard import (
    CHEMIN_APP,
    creer_demande,
    installer_tenant,
    lancer_ecran_connecte,
    texte_affiche,
)

LE_15_JANVIER = datetime(2026, 1, 15)


def test_sans_connexion_seul_le_formulaire_saffiche(base_branchee):
    installer_tenant(base_branchee)

    ecran = AppTest.from_file(CHEMIN_APP, default_timeout=30).run()

    texte = texte_affiche(ecran)
    assert "Espace professionnel" in texte
    assert "Tableau de bord" not in texte
    assert [champ.label for champ in ecran.text_input] == ["Adresse email", "Mot de passe"]


def test_gestionnaire_connecte_arrive_sur_le_tableau_de_bord(base_branchee):
    tenant = installer_tenant(base_branchee)

    ecran = lancer_ecran_connecte(tenant.id)

    assert "Tableau de bord" in texte_affiche(ecran)
    assert ecran.exception == []


def test_barre_laterale_porte_lentreprise_et_le_gestionnaire_connectes(base_branchee):
    tenant = installer_tenant(base_branchee)

    ecran = lancer_ecran_connecte(tenant.id)

    texte = texte_affiche(ecran)
    assert "Événements Étoile" in texte
    assert "Alice Mbarga" in texte


def test_navigation_mene_au_catalogue_puis_aux_demandes(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = lancer_ecran_connecte(tenant.id)

    ecran = next(b for b in ecran.button if b.key == "nav-catalogue").click().run()
    assert "Catalogue des prestations" in texte_affiche(ecran)

    ecran = next(b for b in ecran.button if b.key == "nav-demandes").click().run()
    assert "Demandes reçues" in texte_affiche(ecran)


def test_navigation_naffiche_aucun_compte_a_cote_des_libelles(base_branchee):
    """Un compteur à côté de « Demandes » ou « Catalogue » n'apporte rien au
    gestionnaire et vieillit mal dès qu'il ne se met pas à jour au bon moment :
    seul le libellé de l'écran figure sur le bouton.
    """
    tenant = installer_tenant(base_branchee)
    creer_demande(base_branchee, tenant, LE_15_JANVIER)

    ecran = lancer_ecran_connecte(tenant.id)

    libelles = [bouton.label for bouton in ecran.button if bouton.key.startswith("nav-")]
    assert not any(caractere.isdigit() for libelle in libelles for caractere in libelle)


def test_tenant_disparu_de_la_base_deconnecte_plutot_que_de_planter(base_branchee):
    """Un tenant supprimé entre deux clics ne doit pas laisser un écran cassé"""
    ecran = lancer_ecran_connecte("tenant-qui-nexiste-pas")

    assert "tenant_id" not in ecran.session_state
    assert ecran.exception == []


def test_deconnexion_efface_tout_letat_du_tableau_de_bord(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = lancer_ecran_connecte(tenant.id, ecran="catalogue")

    ecran = next(b for b in ecran.button if b.key == "deconnexion-bouton").click().run()

    assert "tenant_id" not in ecran.session_state
    assert "utilisateur" not in ecran.session_state
    assert "ecran" not in ecran.session_state


def test_aucune_donnee_dune_autre_entreprise_napparait_a_lecran(base_branchee):
    """Le cœur du cloisonnement, vu du gestionnaire : deux entreprises peuplées,
    une seule connectée, et rien de l'autre ne doit se lire.
    """
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    creer_demande(
        base_branchee, etoile, LE_15_JANVIER, nom_prospect="Sylvie Nkoa", total_devis=2_225_000
    )
    creer_demande(
        base_branchee, fanta, LE_15_JANVIER, nom_prospect="Roger Tchoumi", total_devis=9_999_999
    )

    for nom_ecran in ("tableau_de_bord", "demandes", "catalogue"):
        texte = texte_affiche(lancer_ecran_connecte(etoile.id, ecran=nom_ecran))

        assert "Roger Tchoumi" not in texte
        # Le montant est cherche tel que l'ecran l'ecrit, espaces insecables
        # compris : le chercher avec des espaces ordinaires ne prouverait rien.
        assert formater_montant(9_999_999) not in texte
        assert formater_nombre(9_999_999) not in texte
        assert "Fanta Events" not in texte


def test_slug_dune_autre_entreprise_dans_lurl_ne_change_rien(base_branchee):
    """Le prospect est rattaché par le slug de l'URL (D16), le gestionnaire par
    sa connexion : un paramètre d'URL ne doit pas déplacer son tenant.
    """
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    creer_demande(base_branchee, fanta, LE_15_JANVIER, nom_prospect="Roger Tchoumi")

    app = AppTest.from_file(CHEMIN_APP, default_timeout=30)
    app.session_state["tenant_id"] = etoile.id
    app.session_state["utilisateur"] = lancer_ecran_connecte(etoile.id).session_state[
        "utilisateur"
    ]
    app.query_params["slug"] = "fanta"
    ecran = app.run()

    texte = texte_affiche(ecran)
    assert "Événements Étoile" in texte
    assert "Fanta Events" not in texte
    assert "Roger Tchoumi" not in texte
