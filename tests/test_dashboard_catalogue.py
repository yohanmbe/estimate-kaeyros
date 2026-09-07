"""Écran du catalogue : lecture et écriture des prestations.

Ce qui s'écrit ici est la source des montants de toutes les estimations (D01).
Les tests portent donc autant sur ce qui est refusé que sur ce qui est écrit.
"""
from sqlalchemy import select

from src.catalogue.ressources import charger_ressources_actives
from src.db.models import Ressource
from src.presentation.montant import formater_montant
from tests.aide_dashboard import (
    cliquer,
    installer_tenant,
    lancer_ecran_connecte,
    texte_affiche,
)


def ouvrir_catalogue(tenant_id: str):
    return lancer_ecran_connecte(tenant_id, ecran="catalogue")


def remplir(ecran, cle: str, valeur):
    """Renseigne un champ du formulaire, texte ou nombre, par sa clé"""
    for champs in (ecran.text_input, ecran.number_input):
        for champ in champs:
            if champ.key == cle:
                return champ.set_value(valeur)
    raise AssertionError(f"champ introuvable : {cle}")


def test_liste_montre_les_prestations_avec_leur_prix_et_leur_unite(base_branchee):
    tenant = installer_tenant(base_branchee)

    texte = texte_affiche(ouvrir_catalogue(tenant.id))

    assert "Salle des fêtes Le Bastos" in texte
    assert formater_montant(350_000) in texte
    assert "par jour" in texte
    assert "Salle" in texte
    assert "Bastos · 300 places" in texte


def test_filtre_par_categorie_ne_garde_que_la_categorie_choisie(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = ouvrir_catalogue(tenant.id)

    ecran = ecran.segmented_control[0].set_value("mobilier").run()

    texte = texte_affiche(ecran)
    assert "Chaise bâchée blanche" in texte
    assert "Salle des fêtes Le Bastos" not in texte


def test_formulaire_dune_salle_demande_sa_capacite_et_son_quartier(base_branchee):
    """La capacité filtre les salles et le quartier les trie (D17) : le
    formulaire doit les réclamer, une salle sans capacité restant invisible.
    """
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    cles = [champ.key for champ in ecran.text_input] + [
        champ.key for champ in ecran.number_input
    ]
    assert "edition-attribut-quartier" in cles
    assert "edition-attribut-capacite" in cles


def test_formulaire_dune_sonorisation_ne_demande_aucun_attribut(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    ecran = next(s for s in ecran.selectbox if s.key == "edition-categorie").select(
        "sonorisation"
    ).run()

    cles = [champ.key for champ in ecran.text_input] + [
        champ.key for champ in ecran.number_input
    ]
    assert not [cle for cle in cles if cle.startswith("edition-attribut-")]


def test_categorie_choisie_preselectionne_son_unite_habituelle(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    ecran = next(s for s in ecran.selectbox if s.key == "edition-categorie").select(
        "restauration"
    ).run()

    unite = next(s for s in ecran.selectbox if s.key == "edition-unite")
    assert unite.value == "personne"


def test_prestation_ajoutee_apparait_dans_le_catalogue_et_en_base(base_branchee):
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    remplir(ecran, "edition-nom", "Salle polyvalente Mfandena")
    remplir(ecran, "edition-prix", 200_000)
    remplir(ecran, "edition-attribut-capacite", 150)
    remplir(ecran, "edition-attribut-quartier", "Mfandena")
    ecran = cliquer(ecran, "enregistrer-prestation")

    assert any("ajoutée au catalogue" in message.value for message in ecran.success)
    ajoutee = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Salle polyvalente Mfandena")
    )
    assert ajoutee.tenant_id == tenant.id
    assert ajoutee.prix_unitaire == 200_000
    assert ajoutee.attributs == {"capacite": 150, "quartier": "Mfandena"}
    assert ajoutee.actif is True


def test_salle_sans_capacite_est_refusee_avec_son_explication(base_branchee):
    """Une salle sans capacité ne serait jamais proposée au prospect : mieux
    vaut refuser la saisie que créer une prestation invisible.
    """
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    remplir(ecran, "edition-nom", "Salle sans capacité")
    remplir(ecran, "edition-prix", 120_000)
    remplir(ecran, "edition-attribut-quartier", "Odza")
    ecran = cliquer(ecran, "enregistrer-prestation")

    assert any("Capacité" in erreur.value for erreur in ecran.error)
    assert base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Salle sans capacité")
    ) is None


def test_prix_a_zero_est_refuse(base_branchee):
    """Le catalogue est la source des montants : un prix nul produirait une
    estimation fausse présentée comme calculée.
    """
    tenant = installer_tenant(base_branchee)
    ecran = cliquer(ouvrir_catalogue(tenant.id), "ajouter-prestation")

    remplir(ecran, "edition-nom", "Prestation gratuite")
    remplir(ecran, "edition-attribut-capacite", 100)
    remplir(ecran, "edition-attribut-quartier", "Bastos")
    ecran = cliquer(ecran, "enregistrer-prestation")

    assert any("prix unitaire" in erreur.value.lower() for erreur in ecran.error)
    assert base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Prestation gratuite")
    ) is None


def test_prix_modifie_est_enregistre(base_branchee):
    tenant = installer_tenant(base_branchee)
    salle = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Salle des fêtes Le Bastos")
    )
    ecran = cliquer(ouvrir_catalogue(tenant.id), f"modifier-{salle.id}")

    remplir(ecran, "edition-prix", 375_000)
    ecran = cliquer(ecran, "enregistrer-prestation")

    base_branchee.expire_all()
    modifiee = base_branchee.scalar(select(Ressource).where(Ressource.id == salle.id))
    assert modifiee.prix_unitaire == 375_000
    assert modifiee.nom == "Salle des fêtes Le Bastos"


def test_prestation_retiree_disparait_des_options_du_prospect_sans_etre_supprimee(
    base_branchee,
):
    """Retirer désactive : un devis émis garde l'identifiant de la ressource
    dans ses lignes figées (D11), une suppression le rendrait inauditable.
    """
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )
    ecran = ouvrir_catalogue(tenant.id)

    ecran = cliquer(ecran, f"basculer-{chaise.id}")

    base_branchee.expire_all()
    assert any("plus proposée aux prospects" in message.value for message in ecran.success)
    assert base_branchee.scalar(select(Ressource).where(Ressource.id == chaise.id)) is not None
    noms_proposes = [
        ressource.nom for ressource in charger_ressources_actives(base_branchee, tenant.id)
    ]
    assert "Chaise bâchée blanche" not in noms_proposes


def test_prestation_retiree_peut_etre_remise_en_service(base_branchee):
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )
    ecran = cliquer(ouvrir_catalogue(tenant.id), f"basculer-{chaise.id}")

    ecran = cliquer(ecran, f"basculer-{chaise.id}")

    base_branchee.expire_all()
    assert any("de nouveau proposée" in message.value for message in ecran.success)
    noms_proposes = [
        ressource.nom for ressource in charger_ressources_actives(base_branchee, tenant.id)
    ]
    assert "Chaise bâchée blanche" in noms_proposes


def test_prestation_retiree_apparait_dans_son_propre_bloc(base_branchee):
    """Une prestation retirée doit se voir clairement à part de celles encore
    proposées, pas mêlée à la liste active avec un simple badge.
    """
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )

    ecran = cliquer(ouvrir_catalogue(tenant.id), f"basculer-{chaise.id}")

    texte = texte_affiche(ecran)
    assert "Prestations retirées" in texte
    assert any(bouton.key == f"supprimer-{chaise.id}" for bouton in ecran.button)
    assert not any(bouton.key == f"modifier-{chaise.id}" for bouton in ecran.button)


def test_supprimer_une_prestation_retiree_demande_confirmation(base_branchee):
    """Un clic sur Supprimer ne doit rien effacer tout de suite : la
    suppression est définitive, elle réclame un second geste explicite.
    """
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )
    ecran = cliquer(ouvrir_catalogue(tenant.id), f"basculer-{chaise.id}")

    ecran = cliquer(ecran, f"supprimer-{chaise.id}")

    assert "Suppression définitive" in texte_affiche(ecran)
    assert base_branchee.scalar(select(Ressource).where(Ressource.id == chaise.id)) is not None
    assert any(bouton.key == f"confirmer-suppression-{chaise.id}" for bouton in ecran.button)


def test_confirmer_la_suppression_efface_definitivement_la_prestation(base_branchee):
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )
    chaise_id = chaise.id
    ecran = cliquer(ouvrir_catalogue(tenant.id), f"basculer-{chaise_id}")
    ecran = cliquer(ecran, f"supprimer-{chaise_id}")

    ecran = cliquer(ecran, f"confirmer-suppression-{chaise_id}")

    base_branchee.expire_all()
    assert base_branchee.scalar(select(Ressource).where(Ressource.id == chaise_id)) is None
    assert "Chaise bâchée blanche" not in texte_affiche(ecran)


def test_annuler_la_suppression_garde_la_prestation_retiree(base_branchee):
    tenant = installer_tenant(base_branchee)
    chaise = base_branchee.scalar(
        select(Ressource).where(Ressource.nom == "Chaise bâchée blanche")
    )
    ecran = cliquer(ouvrir_catalogue(tenant.id), f"basculer-{chaise.id}")
    ecran = cliquer(ecran, f"supprimer-{chaise.id}")

    ecran = cliquer(ecran, f"annuler-suppression-{chaise.id}")

    base_branchee.expire_all()
    assert base_branchee.scalar(select(Ressource).where(Ressource.id == chaise.id)) is not None
    assert "Chaise bâchée blanche" in texte_affiche(ecran)
    assert not any(bouton.key == f"confirmer-suppression-{chaise.id}" for bouton in ecran.button)


def test_prestation_dune_autre_entreprise_ne_souvre_pas_en_modification(base_branchee):
    """Les identifiants de ressources circulent dans les clés de widgets"""
    etoile = installer_tenant(base_branchee)
    fanta = installer_tenant(base_branchee, slug="fanta", nom="Fanta Events")
    ressource_fanta = base_branchee.scalar(
        select(Ressource).where(
            Ressource.tenant_id == fanta.id, Ressource.nom == "Salle des fêtes Le Bastos"
        )
    )

    ecran = lancer_ecran_connecte(etoile.id, ecran="catalogue")
    ecran.session_state["ressource_en_edition"] = ressource_fanta.id
    ecran = ecran.run()

    assert any("n'existe plus" in message.value for message in ecran.warning)


def test_catalogue_vide_explique_quune_estimation_en_depend(base_branchee):
    tenant = installer_tenant(base_branchee, avec_catalogue=False)

    texte = texte_affiche(ouvrir_catalogue(tenant.id))

    assert "Votre catalogue est vide" in texte
    assert "ne peut rien chiffrer sans catalogue" in texte
