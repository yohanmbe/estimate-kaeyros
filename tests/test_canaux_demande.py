from sqlalchemy import select
from sqlalchemy.orm import Session

from src.canaux.demande import actualiser_besoin, emettre_devis, ouvrir_demande
from src.db.models import ETAT_COMPLETE, ETAT_EN_COURS, Demande, Devis, Prospect, Tenant
from src.moteur.types import LigneDevis, ResultatChiffrage

BESOIN_MARIAGE_300 = {
    "type_evenement": "mariage",
    "date_evenement": "2026-12-12",
    "ville": "Yaoundé",
    "quartier_souhaite": "Bastos",
    "nombre_invites": 300,
    "duree_jours": 1,
}


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_prospect(session: Session, tenant: Tenant) -> Prospect:
    prospect = Prospect(tenant_id=tenant.id, nom="Sylvie Nkoa", telephone="699001122")
    session.add(prospect)
    session.commit()
    return prospect


def resultat_a_deux_lignes(total: int = 2_850_000) -> ResultatChiffrage:
    return ResultatChiffrage(
        lignes=[
            LigneDevis(
                designation="Salle des fêtes Le Bastos",
                quantite=1,
                prix_unitaire=350_000,
                montant=350_000,
                ressource_id="salle-1",
            ),
            LigneDevis(
                designation="Menu complet invité",
                quantite=300,
                prix_unitaire=7_500,
                montant=2_250_000,
                ressource_id="menu-1",
            ),
        ],
        total=total,
        categories_non_satisfaites=[],
        depasse_budget=False,
    )


def ouvrir_demande_pour(session: Session, tenant: Tenant, besoin: dict | None = None):
    prospect = creer_prospect(session, tenant)
    return ouvrir_demande(
        session,
        tenant.id,
        canal="streamlit",
        prospect_id=prospect.id,
        besoin=besoin if besoin is not None else {},
    )


def test_demande_est_ouverte_en_cours_des_que_le_prospect_est_connu(session):
    """Ouverte avant la première question : une conversation interrompue reste
    une demande visible au tableau de bord, donc relançable (D26).
    """
    etoile = creer_tenant(session, "etoile")

    demande = ouvrir_demande_pour(session, etoile)

    enregistree = session.scalar(select(Demande).where(Demande.id == demande.id))
    assert demande.etat == ETAT_EN_COURS
    assert enregistree.tenant_id == etoile.id
    assert enregistree.canal == "streamlit"
    assert enregistree.prospect_id is not None
    assert enregistree.besoin == {}


def test_besoin_actualise_est_relu_tel_quel(session):
    etoile = creer_tenant(session, "etoile")
    demande = ouvrir_demande_pour(session, etoile)

    assert actualiser_besoin(session, etoile.id, demande.id, BESOIN_MARIAGE_300) is True

    enregistree = session.scalar(select(Demande).where(Demande.id == demande.id))
    assert enregistree.besoin == BESOIN_MARIAGE_300


def test_besoin_dune_demande_dun_autre_tenant_nest_jamais_modifie(session):
    """L'identifiant d'une demande circule dans les clés de widgets : le connaître
    ne doit pas suffire à écrire dans l'espace d'une autre entreprise.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    demande_fanta = ouvrir_demande_pour(session, fanta, besoin=BESOIN_MARIAGE_300)

    assert actualiser_besoin(session, etoile.id, demande_fanta.id, {"nombre_invites": 1}) is False

    inchangee = session.scalar(select(Demande).where(Demande.id == demande_fanta.id))
    assert inchangee.besoin == BESOIN_MARIAGE_300


def test_devis_emis_fige_les_lignes_et_le_total_du_chiffrage(session):
    etoile = creer_tenant(session, "etoile")
    demande = ouvrir_demande_pour(session, etoile, besoin=BESOIN_MARIAGE_300)

    recu = emettre_devis(session, etoile.id, demande.id, resultat_a_deux_lignes())

    enregistre = session.scalar(select(Devis).where(Devis.id == recu.id))
    assert recu.total == 2_850_000
    assert recu.devise == "XAF"
    assert enregistre.total == 2_850_000
    assert [ligne["designation"] for ligne in enregistre.lignes] == [
        "Salle des fêtes Le Bastos",
        "Menu complet invité",
    ]
    assert enregistre.lignes[1]["quantite"] == 300
    assert enregistre.lignes[1]["montant"] == 2_250_000
    assert enregistre.date_validite is None


def test_demande_passe_a_complete_quand_son_devis_est_emis(session):
    etoile = creer_tenant(session, "etoile")
    demande = ouvrir_demande_pour(session, etoile, besoin=BESOIN_MARIAGE_300)

    emettre_devis(session, etoile.id, demande.id, resultat_a_deux_lignes())

    enregistree = session.scalar(select(Demande).where(Demande.id == demande.id))
    assert enregistree.etat == ETAT_COMPLETE


def test_reemettre_le_meme_devis_ne_cree_pas_une_seconde_ligne(session):
    """Streamlit rejoue tout le script à chaque interaction : sans cette garde,
    une conversation laissée ouverte accumulerait un devis par rerun et
    gonflerait le montant total du tableau de bord.
    """
    etoile = creer_tenant(session, "etoile")
    demande = ouvrir_demande_pour(session, etoile, besoin=BESOIN_MARIAGE_300)

    recus = [
        emettre_devis(session, etoile.id, demande.id, resultat_a_deux_lignes())
        for _ in range(5)
    ]

    devis_enregistres = session.scalars(
        select(Devis).where(Devis.demande_id == demande.id)
    ).all()
    assert len(devis_enregistres) == 1
    assert {recu.id for recu in recus} == {devis_enregistres[0].id}


def test_besoin_modifie_apres_emission_donne_un_second_devis(session):
    """Les lignes émises ne se réécrivent pas (D11) : un besoin qui change
    produit une nouvelle estimation, et le total du tableau de bord somme bien
    les devis émis (voir DONNEES.md).
    """
    etoile = creer_tenant(session, "etoile")
    demande = ouvrir_demande_pour(session, etoile, besoin=BESOIN_MARIAGE_300)
    premier = emettre_devis(session, etoile.id, demande.id, resultat_a_deux_lignes())

    second = emettre_devis(
        session, etoile.id, demande.id, resultat_a_deux_lignes(total=3_100_000)
    )

    assert second.id != premier.id
    assert len(session.scalars(select(Devis).where(Devis.demande_id == demande.id)).all()) == 2


def test_devis_dune_demande_dun_autre_tenant_nest_jamais_emis(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    demande_fanta = ouvrir_demande_pour(session, fanta, besoin=BESOIN_MARIAGE_300)

    assert emettre_devis(session, etoile.id, demande_fanta.id, resultat_a_deux_lignes()) is None

    assert session.scalars(select(Devis)).all() == []
    inchangee = session.scalar(select(Demande).where(Demande.id == demande_fanta.id))
    assert inchangee.etat == ETAT_EN_COURS
