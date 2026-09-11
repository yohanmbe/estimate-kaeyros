from datetime import datetime

from sqlalchemy.orm import Session

from src.consultation.demandes import (
    compter_demandes_du_tenant,
    consulter_demande,
    lister_demandes,
)
from src.db.models import ETAT_COMPLETE, ETAT_EN_COURS, Demande, Devis, Prospect, Tenant
from src.indicateurs.types import Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))

BESOIN_MARIAGE_300 = {
    "type_evenement": "mariage",
    "date_evenement": "2026-12-12",
    "ville": "Yaoundé",
    "quartier_souhaite": "Bastos",
    "nombre_invites": 300,
    "duree_jours": 1,
}

LIGNES_FIGEES = [
    {
        "designation": "Salle des fêtes Le Bastos",
        "quantite": 1,
        "prix_unitaire": 350_000,
        "montant": 350_000,
        "ressource_id": "salle-1",
    },
    {
        "designation": "Menu complet invité",
        "quantite": 300,
        "prix_unitaire": 7_500,
        "montant": 2_250_000,
        "ressource_id": "menu-1",
    },
]


def creer_tenant(session: Session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_demande(
    session: Session,
    tenant: Tenant,
    date_creation: datetime = datetime(2026, 1, 15),
    besoin: dict | None = None,
    etat: str = ETAT_EN_COURS,
    nom_prospect: str | None = "Sylvie Nkoa",
    prospect: Prospect | None = None,
) -> Demande:
    """Passer un prospect existant (par ex. premiere_demande.prospect) simule
    un même prospect qui revient (voir D47) : nom_prospect est alors ignoré.
    """
    prospect_id = None
    if prospect is not None:
        prospect_id = prospect.id
    elif nom_prospect is not None:
        prospect = Prospect(
            tenant_id=tenant.id,
            nom=nom_prospect,
            telephone="699001122",
            email="sylvie@example.cm",
        )
        session.add(prospect)
        session.flush()
        prospect_id = prospect.id

    demande = Demande(
        tenant_id=tenant.id,
        canal="streamlit",
        prospect_id=prospect_id,
        etat=etat,
        besoin=besoin if besoin is not None else BESOIN_MARIAGE_300,
        date_creation=date_creation,
    )
    session.add(demande)
    session.commit()
    return demande


def creer_devis(
    session: Session,
    tenant: Tenant,
    demande: Demande,
    total: int = 2_600_000,
    date_emission: datetime = datetime(2026, 1, 15),
) -> Devis:
    devis = Devis(
        tenant_id=tenant.id,
        demande_id=demande.id,
        lignes=LIGNES_FIGEES,
        total=total,
        date_emission=date_emission,
    )
    session.add(devis)
    session.commit()
    return devis


def test_liste_presente_la_demande_avec_son_besoin_et_son_prospect(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile, etat=ETAT_COMPLETE)
    creer_devis(session, etoile, demande)

    lignes = lister_demandes(session, etoile.id, PERIODE_JANVIER)

    assert len(lignes) == 1
    ligne = lignes[0]
    assert ligne.type_evenement == "mariage"
    assert ligne.nombre_invites == 300
    assert ligne.quartier_souhaite == "Bastos"
    assert ligne.etat == ETAT_COMPLETE
    assert ligne.prospect.nom == "Sylvie Nkoa"
    assert ligne.prospect.telephone == "699001122"
    assert ligne.total_dernier_devis == 2_600_000
    assert ligne.devise == "XAF"


def test_demande_sans_devis_na_pas_de_montant_plutot_quun_total_a_zero(session):
    """Une conversation en cours n'a pas de montant : afficher zéro laisserait
    croire à une estimation gratuite.
    """
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile)

    ligne = lister_demandes(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.total_dernier_devis is None
    assert ligne.devise is None


def test_liste_montre_le_devis_le_plus_recent_quand_le_besoin_a_change(session):
    """Un besoin modifié après une première estimation en produit une seconde
    (D11) : c'est la dernière que le gestionnaire doit voir dans la liste.
    """
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile, etat=ETAT_COMPLETE)
    creer_devis(session, etoile, demande, total=2_600_000, date_emission=datetime(2026, 1, 15, 10))
    creer_devis(session, etoile, demande, total=3_100_000, date_emission=datetime(2026, 1, 15, 11))

    ligne = lister_demandes(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.total_dernier_devis == 3_100_000


def test_liste_va_de_la_demande_la_plus_recente_a_la_plus_ancienne(session):
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile, date_creation=datetime(2026, 1, 5), nom_prospect="Ancienne")
    creer_demande(session, etoile, date_creation=datetime(2026, 1, 25), nom_prospect="Recente")

    lignes = lister_demandes(session, etoile.id, PERIODE_JANVIER)

    assert [ligne.prospect.nom for ligne in lignes] == ["Recente", "Ancienne"]


def test_liste_limitee_garde_les_plus_recentes(session):
    """Le tableau de bord n'affiche que les cinq dernières demandes"""
    etoile = creer_tenant(session, "etoile")
    for jour in range(1, 8):
        creer_demande(session, etoile, date_creation=datetime(2026, 1, jour))

    lignes = lister_demandes(session, etoile.id, PERIODE_JANVIER, limite=5)

    assert len(lignes) == 5
    assert lignes[0].date_creation == datetime(2026, 1, 7)


def test_liste_hors_periode_ne_remonte_pas(session):
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile, date_creation=datetime(2025, 12, 31))

    assert lister_demandes(session, etoile.id, PERIODE_JANVIER) == []


def test_filtre_par_etat_ne_garde_que_les_demandes_demandees(session):
    etoile = creer_tenant(session, "etoile")
    creer_demande(session, etoile, etat=ETAT_EN_COURS, nom_prospect="En cours")
    creer_demande(session, etoile, etat=ETAT_COMPLETE, nom_prospect="Chiffree")

    lignes = lister_demandes(session, etoile.id, PERIODE_JANVIER, etat=ETAT_COMPLETE)

    assert [ligne.prospect.nom for ligne in lignes] == ["Chiffree"]


def test_liste_ne_contient_jamais_les_demandes_dun_autre_tenant(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    demande_fanta = creer_demande(session, fanta, nom_prospect="Prospect de Fanta")
    creer_devis(session, fanta, demande_fanta)

    assert lister_demandes(session, etoile.id, PERIODE_JANVIER) == []


def test_detail_montre_le_besoin_complet_et_les_lignes_figees_du_devis(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile, etat=ETAT_COMPLETE)
    creer_devis(session, etoile, demande)

    detail = consulter_demande(session, etoile.id, demande.id)

    assert detail.besoin == BESOIN_MARIAGE_300
    assert detail.resume.prospect.email == "sylvie@example.cm"
    assert len(detail.devis) == 1
    lignes = detail.devis[0].lignes
    assert [ligne.designation for ligne in lignes] == [
        "Salle des fêtes Le Bastos",
        "Menu complet invité",
    ]
    assert lignes[1].quantite == 300
    assert lignes[1].montant == 2_250_000
    assert detail.devis[0].total == 2_600_000


def test_detail_liste_les_devis_du_plus_recent_au_plus_ancien(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile, etat=ETAT_COMPLETE)
    creer_devis(session, etoile, demande, total=2_600_000, date_emission=datetime(2026, 1, 15, 10))
    creer_devis(session, etoile, demande, total=3_100_000, date_emission=datetime(2026, 1, 15, 11))

    detail = consulter_demande(session, etoile.id, demande.id)

    assert [devis.total for devis in detail.devis] == [3_100_000, 2_600_000]


def test_detail_dun_prospect_a_sa_premiere_demande_compte_une_demande(session):
    etoile = creer_tenant(session, "etoile")
    demande = creer_demande(session, etoile)

    detail = consulter_demande(session, etoile.id, demande.id)

    assert detail.resume.prospect.nombre_demandes == 1


def test_detail_dun_prospect_revenu_compte_toutes_ses_demandes(session):
    """Même prospect (même ligne, voir D47), deux demandes à des dates
    différentes : le détail de l'une ou l'autre doit montrer les deux."""
    etoile = creer_tenant(session, "etoile")
    premiere = creer_demande(session, etoile, date_creation=datetime(2026, 1, 5))
    seconde = creer_demande(
        session, etoile, date_creation=datetime(2026, 1, 20), prospect=premiere.prospect
    )

    detail_premiere = consulter_demande(session, etoile.id, premiere.id)
    detail_seconde = consulter_demande(session, etoile.id, seconde.id)

    assert detail_premiere.resume.prospect.nombre_demandes == 2
    assert detail_seconde.resume.prospect.nombre_demandes == 2


def test_demande_dun_autre_tenant_est_introuvable_meme_avec_son_identifiant(session):
    """Les identifiants de demandes circulent dans les clés de widgets :
    connaître celui d'une autre entreprise ne doit donner accès à rien.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    demande_fanta = creer_demande(session, fanta)

    assert consulter_demande(session, etoile.id, demande_fanta.id) is None


def test_prospect_rattache_a_un_autre_tenant_nest_jamais_affiche(session):
    """La clé étrangère ne garantit pas que le prospect appartient au même
    tenant : seul le filtre le fait. La demande s'affiche alors sans
    coordonnées plutôt qu'avec celles d'une autre entreprise.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    prospect_fanta = Prospect(tenant_id=fanta.id, nom="Prospect de Fanta", telephone="600000000")
    session.add(prospect_fanta)
    session.flush()
    session.add(
        Demande(
            tenant_id=etoile.id,
            canal="streamlit",
            prospect_id=prospect_fanta.id,
            besoin=BESOIN_MARIAGE_300,
            date_creation=datetime(2026, 1, 15),
        )
    )
    session.commit()

    ligne = lister_demandes(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.prospect is None


def test_compte_du_tenant_ignore_la_periode_et_les_autres_tenants(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_demande(session, etoile, date_creation=datetime(2025, 6, 1))
    creer_demande(session, etoile, date_creation=datetime(2026, 1, 15))
    creer_demande(session, fanta, date_creation=datetime(2026, 1, 15))

    assert compter_demandes_du_tenant(session, etoile.id) == 2
