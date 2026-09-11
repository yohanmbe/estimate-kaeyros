"""Lecture des prospects, le carnet d'adresses du gestionnaire (voir D49).

L'écran qui s'en sert est testé dans tests/test_dashboard_prospects.py. Ici on
vérifie les règles de la couche de lecture elle-même : ce que la période
borne et ce qu'elle ne borne pas, ce que la recherche trouve, et le
cloisonnement entre entreprises clientes.
"""
from datetime import datetime

from src.consultation.prospects import consulter_prospect, lister_prospects
from src.db.models import ETAT_COMPLETE, ETAT_EN_COURS, Demande, Devis, Prospect, Tenant
from src.indicateurs.types import Periode

PERIODE_JANVIER = Periode(debut=datetime(2026, 1, 1), fin=datetime(2026, 1, 31, 23, 59, 59))
PERIODE_LARGE = Periode(debut=datetime(2020, 1, 1), fin=datetime(2030, 12, 31))
LE_10_JANVIER = datetime(2026, 1, 10)
LE_20_JANVIER = datetime(2026, 1, 20)


def creer_tenant(session, slug: str) -> Tenant:
    tenant = Tenant(nom=f"Entreprise {slug}", slug=slug)
    session.add(tenant)
    session.commit()
    return tenant


def creer_prospect(
    session,
    tenant: Tenant,
    date_creation: datetime = LE_10_JANVIER,
    nom: str = "Sylvie Nkoa",
    telephone: str = "699001122",
    email: str | None = "sylvie@example.cm",
    consentement_contact: bool = True,
) -> Prospect:
    prospect = Prospect(
        tenant_id=tenant.id,
        nom=nom,
        telephone=telephone,
        email=email,
        consentement_contact=consentement_contact,
        date_creation=date_creation,
    )
    session.add(prospect)
    session.commit()
    return prospect


def creer_demande(
    session,
    tenant: Tenant,
    prospect: Prospect | None,
    date_creation: datetime = LE_10_JANVIER,
    total_devis: int | None = None,
) -> Demande:
    demande = Demande(
        tenant_id=tenant.id,
        canal="streamlit",
        prospect_id=prospect.id if prospect else None,
        etat=ETAT_COMPLETE if total_devis is not None else ETAT_EN_COURS,
        besoin={"type_evenement": "mariage", "nombre_invites": 300},
        date_creation=date_creation,
    )
    session.add(demande)
    session.flush()
    if total_devis is not None:
        session.add(
            Devis(
                tenant_id=tenant.id,
                demande_id=demande.id,
                lignes=[],
                total=total_devis,
                date_emission=date_creation,
            )
        )
    session.commit()
    return demande


def test_liste_va_du_prospect_le_plus_recent_au_plus_ancien(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, LE_10_JANVIER, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(session, etoile, LE_20_JANVIER, nom="Jean Etoundi", telephone="677445566")

    prospects = lister_prospects(session, etoile.id, PERIODE_JANVIER)

    assert [prospect.nom for prospect in prospects] == ["Jean Etoundi", "Sylvie Nkoa"]


def test_limite_ne_garde_que_les_premiers(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, LE_10_JANVIER, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(session, etoile, LE_20_JANVIER, nom="Jean Etoundi", telephone="677445566")

    prospects = lister_prospects(session, etoile.id, PERIODE_JANVIER, limite=1)

    assert [prospect.nom for prospect in prospects] == ["Jean Etoundi"]


def test_chaque_ligne_porte_son_nombre_de_demandes_et_la_date_de_la_derniere(session):
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile)
    creer_demande(session, etoile, prospect, LE_10_JANVIER)
    creer_demande(session, etoile, prospect, LE_20_JANVIER)

    ligne = lister_prospects(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.nombre_demandes == 2
    assert ligne.date_derniere_demande == LE_20_JANVIER


def test_prospect_sans_aucune_demande_est_liste_sans_compte_ni_date(session):
    """La fiche existe dès le formulaire rempli : la conversation peut s'être
    arrêtée avant d'ouvrir une demande, et ce prospect reste à rappeler.
    """
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile)

    ligne = lister_prospects(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.nombre_demandes == 0
    assert ligne.date_derniere_demande is None


def test_prospect_revenu_ne_fait_quune_seule_ligne(session):
    """Même téléphone, deux demandes : une personne, pas deux (voir D47)"""
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile)
    creer_demande(session, etoile, prospect, LE_10_JANVIER)
    creer_demande(session, etoile, prospect, LE_20_JANVIER)

    prospects = lister_prospects(session, etoile.id, PERIODE_JANVIER)

    assert len(prospects) == 1
    assert prospects[0].nombre_demandes == 2


def test_le_compte_de_demandes_ignore_la_periode_affichee(session):
    """« Cette personne est revenue trois fois » est un fait sur elle, pas sur
    le mois qu'on regarde (voir D47) : la période borne la liste, pas le compte.
    """
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile, LE_10_JANVIER)
    creer_demande(session, etoile, prospect, LE_10_JANVIER)
    creer_demande(session, etoile, prospect, datetime(2025, 6, 1))

    ligne = lister_prospects(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.nombre_demandes == 2


def test_prospect_cree_hors_periode_nest_pas_liste(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, datetime(2025, 6, 1))

    assert lister_prospects(session, etoile.id, PERIODE_JANVIER) == []


def test_recherche_par_nom_ignore_la_casse_et_accepte_un_fragment(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(session, etoile, nom="Jean Etoundi", telephone="677445566")

    trouves = lister_prospects(session, etoile.id, PERIODE_JANVIER, recherche="nko")

    assert [prospect.nom for prospect in trouves] == ["Sylvie Nkoa"]


def test_recherche_par_telephone_tolere_les_espaces_de_la_saisie(session):
    """Le gestionnaire recopie « 699 00 11 » depuis son écran d'appel, la base
    stocke le numéro d'un seul tenant.
    """
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(session, etoile, nom="Jean Etoundi", telephone="677445566")

    trouves = lister_prospects(session, etoile.id, PERIODE_JANVIER, recherche="699 00 11")

    assert [prospect.nom for prospect in trouves] == ["Sylvie Nkoa"]


def test_recherche_vide_ou_blanche_ne_filtre_rien(session):
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile)

    assert len(lister_prospects(session, etoile.id, PERIODE_JANVIER, recherche="")) == 1
    assert len(lister_prospects(session, etoile.id, PERIODE_JANVIER, recherche="   ")) == 1


def test_une_recherche_contenant_un_pourcent_ne_renvoie_pas_tout_le_carnet(session):
    """% est un joker de LIKE : sans échappement, le chercher renverrait tout"""
    etoile = creer_tenant(session, "etoile")
    creer_prospect(session, etoile, nom="Sylvie Nkoa", telephone="699001122")
    creer_prospect(session, etoile, nom="Jean Etoundi", telephone="677445566")

    assert lister_prospects(session, etoile.id, PERIODE_JANVIER, recherche="%") == []


def test_fiche_dun_prospect_porte_ses_demandes_de_la_plus_recente_a_la_plus_ancienne(session):
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile)
    ancienne = creer_demande(session, etoile, prospect, LE_10_JANVIER)
    recente = creer_demande(session, etoile, prospect, LE_20_JANVIER, total_devis=2_225_000)

    detail = consulter_prospect(session, etoile.id, prospect.id)

    assert [demande.id for demande in detail.demandes] == [recente.id, ancienne.id]
    assert detail.demandes[0].total_dernier_devis == 2_225_000
    assert detail.resume.nombre_demandes == 2
    assert detail.resume.date_derniere_demande == LE_20_JANVIER


def test_fiche_nest_bornee_par_aucune_periode(session):
    """On regarde une personne, pas un mois : son historique est entier"""
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile, LE_10_JANVIER)
    creer_demande(session, etoile, prospect, datetime(2021, 3, 1))
    creer_demande(session, etoile, prospect, LE_20_JANVIER)

    detail = consulter_prospect(session, etoile.id, prospect.id)

    assert len(detail.demandes) == 2


def test_fiche_dun_prospect_sans_demande_est_vide_mais_existe(session):
    etoile = creer_tenant(session, "etoile")
    prospect = creer_prospect(session, etoile)

    detail = consulter_prospect(session, etoile.id, prospect.id)

    assert detail.demandes == ()
    assert detail.resume.nom == "Sylvie Nkoa"
    assert detail.resume.date_derniere_demande is None


def test_liste_ignore_les_prospects_dune_autre_entreprise(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    creer_prospect(session, fanta, nom="Roger Tchoumi", telephone="655443322")

    assert lister_prospects(session, etoile.id, PERIODE_LARGE) == []


def test_fiche_dun_prospect_dune_autre_entreprise_reste_introuvable(session):
    """Connaître l'identifiant ne doit donner accès à rien : il circule dans
    les clés de widgets.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    prospect_fanta = creer_prospect(session, fanta, nom="Roger Tchoumi", telephone="655443322")

    assert consulter_prospect(session, etoile.id, prospect_fanta.id) is None


def test_une_demande_dune_autre_entreprise_napparait_pas_sous_la_fiche(session):
    """Le prospect_id d'une demande ne suffit pas : la clé étrangère ne dit
    rien du locataire, seul le filtre le dit.
    """
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    prospect = creer_prospect(session, etoile)
    creer_demande(session, etoile, prospect, LE_10_JANVIER)
    # Une demande de fanta rattachée au prospect d'etoile : incohérence que
    # seul le filtre sur tenant_id rattrape.
    creer_demande(session, fanta, prospect, LE_20_JANVIER, total_devis=9_999_999)

    detail = consulter_prospect(session, etoile.id, prospect.id)

    assert len(detail.demandes) == 1
    assert detail.demandes[0].total_dernier_devis is None


def test_le_compte_de_demandes_ignore_celles_dune_autre_entreprise(session):
    etoile = creer_tenant(session, "etoile")
    fanta = creer_tenant(session, "fanta")
    prospect = creer_prospect(session, etoile)
    creer_demande(session, etoile, prospect, LE_10_JANVIER)
    creer_demande(session, fanta, prospect, LE_20_JANVIER)

    ligne = lister_prospects(session, etoile.id, PERIODE_JANVIER)[0]

    assert ligne.nombre_demandes == 1
