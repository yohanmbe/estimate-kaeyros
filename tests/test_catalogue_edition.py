import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.catalogue.edition import (
    SaisieRessource,
    basculer_activation,
    compter_ressources,
    creer_ressource,
    lister_pour_gestion,
    modifier_ressource,
    supprimer_ressource,
    valider_saisie,
)
from src.catalogue.ressources import charger_ressources_actives
from src.db.models import Ressource, Tenant

SALLE_BASTOS = SaisieRessource(
    nom="Salle des fêtes Le Bastos",
    categorie="salle",
    unite_facturation="jour",
    prix_unitaire=350_000,
    attributs={"capacite": 300, "quartier": "Bastos"},
)

MENU = SaisieRessource(
    nom="Menu complet invité",
    categorie="restauration",
    unite_facturation="personne",
    prix_unitaire=7_500,
    attributs={},
)


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def test_saisie_complete_est_acceptee():
    assert valider_saisie(SALLE_BASTOS) == []
    assert valider_saisie(MENU) == []


def test_nom_vide_est_refuse():
    saisie = SaisieRessource(
        nom="   ", categorie="salle", unite_facturation="jour", prix_unitaire=1,
        attributs={"capacite": 10, "quartier": "Bastos"},
    )

    assert any("nom" in raison.lower() for raison in valider_saisie(saisie))


def test_prix_nul_ou_negatif_est_refuse():
    """Le catalogue est la seule source des montants (D01) : un prix nul
    produirait une estimation fausse présentée comme calculée.
    """
    for prix in (0, -5_000):
        saisie = SaisieRessource(
            nom="Sonorisation", categorie="sonorisation", unite_facturation="forfait",
            prix_unitaire=prix, attributs={},
        )

        assert any("prix" in raison.lower() for raison in valider_saisie(saisie))


def test_categorie_hors_vocabulaire_est_refusee():
    saisie = SaisieRessource(
        nom="Nuit d'hôtel", categorie="hebergement", unite_facturation="jour",
        prix_unitaire=45_000, attributs={},
    )

    assert any("Catégorie inconnue" in raison for raison in valider_saisie(saisie))


def test_unite_hors_vocabulaire_est_refusee():
    saisie = SaisieRessource(
        nom="Décoration", categorie="decoration", unite_facturation="semaine",
        prix_unitaire=150_000, attributs={},
    )

    assert any("Unité de facturation inconnue" in raison for raison in valider_saisie(saisie))


def test_salle_sans_capacite_est_refusee():
    """Sans capacité, la salle ne passerait jamais le filtre du moteur (D17) :
    elle serait au catalogue sans jamais être proposée à personne.
    """
    saisie = SaisieRessource(
        nom="Salle sans capacité", categorie="salle", unite_facturation="jour",
        prix_unitaire=120_000, attributs={"quartier": "Odza"},
    )

    assert any("Capacité" in raison for raison in valider_saisie(saisie))


def test_salle_sans_quartier_est_refusee():
    saisie = SaisieRessource(
        nom="Salle sans quartier", categorie="salle", unite_facturation="jour",
        prix_unitaire=120_000, attributs={"capacite": 200},
    )

    assert any("Quartier" in raison for raison in valider_saisie(saisie))


def test_capacite_non_entiere_est_refusee():
    saisie = SaisieRessource(
        nom="Salle", categorie="salle", unite_facturation="jour", prix_unitaire=120_000,
        attributs={"capacite": "beaucoup", "quartier": "Odza"},
    )

    assert any("Capacité" in raison for raison in valider_saisie(saisie))


def test_toutes_les_raisons_sont_renvoyees_dun_coup():
    """Le gestionnaire corrige son formulaire en une fois, pas erreur par erreur"""
    saisie = SaisieRessource(
        nom="", categorie="hebergement", unite_facturation="semaine", prix_unitaire=0,
        attributs={},
    )

    assert len(valider_saisie(saisie)) == 4


def test_style_du_mobilier_reste_facultatif():
    saisie = SaisieRessource(
        nom="Chaise", categorie="mobilier", unite_facturation="unite", prix_unitaire=500,
        attributs={},
    )

    assert valider_saisie(saisie) == []


def test_prestation_creee_est_proposee_au_prospect(session):
    etoile = creer_tenant(session, "etoile")

    creer_ressource(session, etoile.id, SALLE_BASTOS)

    proposees = [r.nom for r in charger_ressources_actives(session, etoile.id)]
    assert proposees == ["Salle des fêtes Le Bastos"]


def test_nom_est_enregistre_sans_ses_espaces_de_bord(session):
    etoile = creer_tenant(session, "etoile")
    saisie = SaisieRessource(
        nom="  Menu complet  ", categorie="restauration", unite_facturation="personne",
        prix_unitaire=7_500, attributs={},
    )

    creer_ressource(session, etoile.id, saisie)

    assert session.scalar(select(Ressource)).nom == "Menu complet"


def test_creation_dune_saisie_invalide_est_refusee_meme_sans_passer_par_lecran(session):
    """Le contrôle ne dépend pas de l'écran : la base ne doit jamais recevoir
    une prestation qu'aucun prospect ne pourrait se voir proposer.
    """
    etoile = creer_tenant(session, "etoile")
    saisie = SaisieRessource(
        nom="Salle sans capacité", categorie="salle", unite_facturation="jour",
        prix_unitaire=120_000, attributs={"quartier": "Odza"},
    )

    with pytest.raises(ValueError):
        creer_ressource(session, etoile.id, saisie)

    assert session.scalars(select(Ressource)).all() == []


def test_liste_de_gestion_montre_aussi_les_prestations_retirees(session):
    """Le gestionnaire doit voir ce qu'il a retiré pour pouvoir le remettre,
    là où le prospect ne voit que les prestations actives.
    """
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)
    basculer_activation(session, etoile.id, identifiant)

    gestion = lister_pour_gestion(session, etoile.id)

    assert [(r.nom, r.actif) for r in gestion] == [("Salle des fêtes Le Bastos", False)]
    assert charger_ressources_actives(session, etoile.id) == []


def test_liste_de_gestion_filtre_par_categorie(session):
    etoile = creer_tenant(session, "etoile")
    creer_ressource(session, etoile.id, SALLE_BASTOS)
    creer_ressource(session, etoile.id, MENU)

    salles = lister_pour_gestion(session, etoile.id, categorie="salle")

    assert [r.nom for r in salles] == ["Salle des fêtes Le Bastos"]


def test_prix_modifie_est_celui_que_le_moteur_lira(session):
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)

    assert modifier_ressource(
        session, etoile.id, identifiant,
        SaisieRessource(
            nom=SALLE_BASTOS.nom, categorie="salle", unite_facturation="jour",
            prix_unitaire=375_000, attributs=SALLE_BASTOS.attributs,
        ),
    )

    assert charger_ressources_actives(session, etoile.id)[0].prix_unitaire == 375_000


def test_retrait_puis_remise_en_service_font_un_aller_retour(session):
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)

    basculer_activation(session, etoile.id, identifiant)
    assert lister_pour_gestion(session, etoile.id)[0].actif is False

    basculer_activation(session, etoile.id, identifiant)
    assert lister_pour_gestion(session, etoile.id)[0].actif is True


def test_retrait_ne_supprime_jamais_la_ligne(session):
    """Un devis émis garde l'identifiant de la ressource dans ses lignes
    figées (D11) : une suppression dure le rendrait inauditable.
    """
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)

    basculer_activation(session, etoile.id, identifiant)

    assert session.scalar(select(Ressource).where(Ressource.id == identifiant)) is not None


def test_catalogue_dun_autre_tenant_nest_jamais_liste(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_ressource(session, fanta.id, SALLE_BASTOS)

    assert lister_pour_gestion(session, etoile.id) == []
    assert compter_ressources(session, etoile.id) == 0


def test_prestation_dun_autre_tenant_nest_jamais_modifiee(session):
    """Les identifiants de ressources circulent dans les clés de widgets :
    connaître celui d'une autre entreprise ne doit rien permettre d'écrire.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    identifiant = creer_ressource(session, fanta.id, SALLE_BASTOS)

    modifiee = modifier_ressource(
        session, etoile.id, identifiant,
        SaisieRessource(
            nom="Volée", categorie="salle", unite_facturation="jour", prix_unitaire=1,
            attributs={"capacite": 1, "quartier": "Ailleurs"},
        ),
    )

    assert modifiee is False
    inchangee = session.scalar(select(Ressource).where(Ressource.id == identifiant))
    assert inchangee.nom == "Salle des fêtes Le Bastos"
    assert inchangee.prix_unitaire == 350_000


def test_prestation_dun_autre_tenant_nest_jamais_retiree(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    identifiant = creer_ressource(session, fanta.id, SALLE_BASTOS)

    assert basculer_activation(session, etoile.id, identifiant) is False

    assert session.scalar(select(Ressource).where(Ressource.id == identifiant)).actif is True


def test_prestation_retiree_peut_etre_supprimee_definitivement(session):
    """Devis.lignes est un instantané JSON figé à l'émission, pas une clé
    étrangère vers ressource (D11) : rien n'empêche de supprimer pour de bon
    une prestation déjà retirée du catalogue.
    """
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)
    basculer_activation(session, etoile.id, identifiant)

    assert supprimer_ressource(session, etoile.id, identifiant) is True

    assert session.scalar(select(Ressource).where(Ressource.id == identifiant)) is None


def test_prestation_encore_active_nest_jamais_supprimee(session):
    """La suppression n'est proposée à l'écran que depuis le bloc des
    prestations retirées ; le même garde-fou vit dans la fonction d'écriture,
    au cas où un identifiant actif serait deviné dans une clé de widget.
    """
    etoile = creer_tenant(session, "etoile")
    identifiant = creer_ressource(session, etoile.id, SALLE_BASTOS)

    assert supprimer_ressource(session, etoile.id, identifiant) is False

    assert session.scalar(select(Ressource).where(Ressource.id == identifiant)) is not None


def test_prestation_dun_autre_tenant_nest_jamais_supprimee(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    identifiant = creer_ressource(session, fanta.id, SALLE_BASTOS)
    basculer_activation(session, fanta.id, identifiant)

    assert supprimer_ressource(session, etoile.id, identifiant) is False

    assert session.scalar(select(Ressource).where(Ressource.id == identifiant)) is not None
