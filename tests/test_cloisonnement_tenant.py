"""Preuve que rien ne peut renvoyer les données d'une autre entreprise cliente.

Trois filets, du plus concret au plus général :

1. chaque fonction de lecture et d'écriture est exercée sous l'écouteur SQL de
   conftest.py, qui lève dès qu'une requête touche une table métier sans
   filtrer sur tenant_id ;
2. l'écouteur est lui-même testé sur une requête volontairement fautive, sans
   quoi un filet troué passerait pour un filet solide ;
3. les signatures sont inspectées : toute fonction publique qui reçoit une
   session doit aussi recevoir un tenant_id, sans valeur par défaut.

Ce que cet ensemble ne garantit pas : l'écouteur ne voit que les requêtes
qu'un test exécute réellement, et la garde de signature ne détecte pas un
paramètre reçu puis ignoré. L'oubli devient improbable, pas impossible.
"""
import importlib
import inspect
import pkgutil
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import src
from src.canaux.demande import actualiser_besoin, emettre_devis, ouvrir_demande
from src.canaux.prospect import enregistrer_prospect
from src.catalogue.edition import (
    SaisieRessource,
    basculer_activation,
    compter_ressources,
    creer_ressource,
    lister_pour_gestion,
    modifier_ressource,
)
from src.catalogue.ressources import charger_modele_evenement, charger_ressources_actives
from src.consultation.demandes import (
    compter_demandes_du_tenant,
    consulter_demande,
    lister_demandes,
)
from src.db.models import Prospect, Ressource, Tenant
from src.indicateurs.chiffrage import calculer_taux_demandes_chiffrees
from src.indicateurs.demandes import compter_demandes, repartir_par_tranche_invites
from src.indicateurs.devis import calculer_montant_moyen, calculer_montant_total
from src.indicateurs.prospects import calculer_taux_consentement_contact
from src.indicateurs.types import Periode
from src.moteur.types import LigneDevis, ResultatChiffrage
from tests.conftest import RequeteNonCloisonnee

PERIODE = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 12, 31))

# Paquets dont toute fonction publique prenant une session doit exiger un
# tenant_id. src/moteur et src/orchestration n'y figurent pas : ils ne touchent
# jamais la base, c'est justement leur définition.
PAQUETS_SURVEILLES = ("src.canaux", "src.catalogue", "src.consultation", "src.indicateurs")

# Deux fonctions reçoivent une session sans tenant_id, et c'est correct : ce
# sont elles qui établissent le tenant. Les lister ici les rend visibles à la
# relecture au lieu de les laisser passer en silence.
DEROGATIONS = {
    ("src.canaux.tenant", "resoudre_tenant"): "résout le tenant depuis le slug de l'URL",
    ("src.catalogue.provisionnement", "provisionner_tenant"): "crée le tenant lui-même",
}


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def resultat_a_une_ligne() -> ResultatChiffrage:
    return ResultatChiffrage(
        lignes=[
            LigneDevis(
                designation="Salle des fêtes Le Bastos",
                quantite=1,
                prix_unitaire=350_000,
                montant=350_000,
                ressource_id="salle-1",
            )
        ],
        total=350_000,
        categories_non_satisfaites=[],
        depasse_budget=False,
    )


def test_lecture_dune_table_metier_sans_filtre_est_bien_detectee(session, requetes_cloisonnees):
    """Auto-test du filet : sans lui, un écouteur cassé validerait tout.

    La requête ci-dessous est exactement l'oubli qu'on cherche à rendre
    impossible — lire une table métier sans son tenant_id.
    """
    creer_tenant(session, "etoile")

    with pytest.raises(RequeteNonCloisonnee):
        session.scalars(select(Prospect)).all()


def test_filtre_sur_un_autre_champ_ne_suffit_pas_a_tromper_le_filet(session, requetes_cloisonnees):
    creer_tenant(session, "etoile")

    with pytest.raises(RequeteNonCloisonnee):
        session.scalars(select(Ressource).where(Ressource.categorie == "salle")).all()


def test_ecriture_de_la_demande_et_du_devis_filtre_toujours_sur_le_tenant(
    session, requetes_cloisonnees
):
    etoile = creer_tenant(session, "etoile")
    prospect = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", None, consentement_contact=True
    )

    demande = ouvrir_demande(
        session, etoile.id, canal="streamlit", prospect_id=prospect.id, besoin={}
    )
    actualiser_besoin(session, etoile.id, demande.id, {"nombre_invites": 300})
    emettre_devis(session, etoile.id, demande.id, resultat_a_une_ligne())


def test_lecture_des_demandes_par_le_gestionnaire_filtre_toujours_sur_le_tenant(
    session, requetes_cloisonnees
):
    etoile = creer_tenant(session, "etoile")
    prospect = enregistrer_prospect(
        session, etoile.id, "Sylvie Nkoa", "699001122", None, consentement_contact=True
    )
    demande = ouvrir_demande(
        session, etoile.id, canal="streamlit", prospect_id=prospect.id, besoin={}
    )
    emettre_devis(session, etoile.id, demande.id, resultat_a_une_ligne())

    lister_demandes(session, etoile.id, PERIODE)
    lister_demandes(session, etoile.id, PERIODE, limite=5)
    consulter_demande(session, etoile.id, demande.id)
    compter_demandes_du_tenant(session, etoile.id)


def test_lecture_du_catalogue_filtre_toujours_sur_le_tenant(session, requetes_cloisonnees):
    etoile = creer_tenant(session, "etoile")

    charger_ressources_actives(session, etoile.id)
    charger_modele_evenement(session, etoile.id, "Mariage")


def test_edition_du_catalogue_filtre_toujours_sur_le_tenant(session, requetes_cloisonnees):
    etoile = creer_tenant(session, "etoile")
    saisie = SaisieRessource(
        nom="Salle des fêtes Le Bastos",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=350_000,
        attributs={"capacite": 300, "quartier": "Bastos"},
    )

    identifiant = creer_ressource(session, etoile.id, saisie)
    lister_pour_gestion(session, etoile.id)
    lister_pour_gestion(session, etoile.id, categorie="salle")
    compter_ressources(session, etoile.id)
    modifier_ressource(session, etoile.id, identifiant, saisie)
    basculer_activation(session, etoile.id, identifiant)


def test_les_six_indicateurs_filtrent_tous_sur_le_tenant(session, requetes_cloisonnees):
    etoile = creer_tenant(session, "etoile")

    compter_demandes(session, etoile.id, PERIODE)
    repartir_par_tranche_invites(session, etoile.id, PERIODE)
    calculer_montant_total(session, etoile.id, PERIODE)
    calculer_montant_moyen(session, etoile.id, PERIODE)
    calculer_taux_demandes_chiffrees(session, etoile.id, PERIODE)
    calculer_taux_consentement_contact(session, etoile.id, PERIODE)


def fonctions_publiques_prenant_une_session():
    """Parcourt les paquets surveillés et renvoie (module, nom, signature)"""
    racine = Path(src.__file__).parent
    for paquet in PAQUETS_SURVEILLES:
        chemin = racine / paquet.split(".")[-1]
        for module_info in pkgutil.iter_modules([str(chemin)]):
            nom_module = f"{paquet}.{module_info.name}"
            module = importlib.import_module(nom_module)
            for nom, fonction in inspect.getmembers(module, inspect.isfunction):
                if nom.startswith("_") or fonction.__module__ != nom_module:
                    continue
                signature = inspect.signature(fonction)
                if any(
                    parametre.annotation is Session
                    for parametre in signature.parameters.values()
                ):
                    yield nom_module, nom, signature


def test_toute_fonction_touchant_la_base_exige_un_tenant_id(session):
    """Garde de signature : un tenant_id qu'on ne peut pas oublier de passer.

    Le paramètre est exigé sans valeur par défaut, pour qu'aucun appel ne
    puisse le laisser tomber et retomber sur un comportement global.
    """
    manquantes = []
    for nom_module, nom, signature in fonctions_publiques_prenant_une_session():
        if (nom_module, nom) in DEROGATIONS:
            continue
        parametre = signature.parameters.get("tenant_id")
        if parametre is None or parametre.default is not inspect.Parameter.empty:
            manquantes.append(f"{nom_module}.{nom}{signature}")

    assert manquantes == []


def test_la_garde_de_signature_inspecte_vraiment_des_fonctions(session):
    """Sans ce garde-fou, un parcours cassé ne trouverait rien et validerait tout"""
    inspectees = {
        f"{nom_module}.{nom}"
        for nom_module, nom, _ in fonctions_publiques_prenant_une_session()
    }

    assert "src.consultation.demandes.consulter_demande" in inspectees
    assert "src.canaux.demande.emettre_devis" in inspectees
    assert "src.indicateurs.devis.calculer_montant_total" in inspectees
    assert len(inspectees) >= 12


def test_chaque_derogation_designe_une_fonction_qui_existe_encore(session):
    """Une dérogation qui survit à la fonction qu'elle couvrait masquerait un oubli"""
    for (nom_module, nom), raison in DEROGATIONS.items():
        module = importlib.import_module(nom_module)

        assert hasattr(module, nom), f"{nom_module}.{nom} n'existe plus"
        assert raison
