"""Enregistrement de la demande et de son devis pendant la conversation.

Le canal Streamlit fait vivre le besoin en mémoire de session ; ce module est le
seul endroit qui l'écrit en base, à côté de prospect.py. Sans lui, une
conversation ne laisserait aucune trace : ni relance commerciale possible, ni
indicateur à afficher au gestionnaire.

Trois règles s'y appliquent :
- la demande est ouverte tôt, dès que le prospect est connu, pour qu'une
  conversation interrompue reste visible au tableau de bord ;
- les lignes du devis sont figées à l'émission, jamais recalculées ensuite (D11) ;
- tenant_id est exigé partout et filtre chaque requête, y compris les écritures
  adressées par identifiant (voir CLAUDE.md, Multi-locataires).
"""
from dataclasses import asdict

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.canaux.types import DemandeOuverte, DevisEmis
from src.db.models import ETAT_COMPLETE, ETAT_EN_COURS, Demande, Devis
from src.moteur.types import ResultatChiffrage


def ouvrir_demande(
    session: Session,
    tenant_id: str,
    canal: str,
    prospect_id: str,
    besoin: dict,
) -> DemandeOuverte:
    """Ouvre la demande au début de la conversation, avant la première question.

    Ouverte ici et non au moment du chiffrage : une conversation abandonnée en
    route doit rester une demande qualifiée que le commercial peut relancer
    (voir le cahier des charges et D26), pas une trace perdue.
    """
    demande = Demande(
        tenant_id=tenant_id,
        canal=canal,
        prospect_id=prospect_id,
        etat=ETAT_EN_COURS,
        besoin=besoin,
    )
    session.add(demande)
    # Lu après le flush, qui attribue l'identifiant, mais avant le commit :
    # le commit périme l'objet, et la relecture qui suivrait porterait sur la
    # seule clé primaire, sans filtre tenant_id (voir tests/conftest.py).
    session.flush()
    ouverte = DemandeOuverte(id=demande.id, etat=demande.etat)
    session.commit()
    return ouverte


def actualiser_besoin(session: Session, tenant_id: str, demande_id: str, besoin: dict) -> bool:
    """Remplace le besoin enregistré par son état courant, False si demande introuvable.

    Le filtre porte sur l'identifiant ET le tenant : un identifiant de demande
    appartenant à une autre entreprise ne doit rien modifier, et rowcount le dit
    plutôt que de laisser croire à une réussite silencieuse.
    """
    resultat = session.execute(
        update(Demande)
        .where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
        .values(besoin=besoin)
    )
    session.commit()
    return resultat.rowcount == 1


def enregistrer_complements(
    session: Session,
    tenant_id: str,
    demande_id: str,
    besoins_hors_catalogue: str | None,
    commentaire: str | None,
) -> bool:
    """Enregistre ce que le prospect a écrit en clair, False si demande introuvable.

    Même filtrage que actualiser_besoin : l'identifiant seul ne suffit pas,
    le tenant est vérifié pour qu'une demande d'une autre entreprise reste
    hors d'atteinte.
    """
    resultat = session.execute(
        update(Demande)
        .where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
        .values(
            besoins_hors_catalogue=besoins_hors_catalogue,
            commentaire=commentaire,
        )
    )
    session.commit()
    return resultat.rowcount == 1


def emettre_devis(
    session: Session, tenant_id: str, demande_id: str, resultat: ResultatChiffrage
) -> DevisEmis | None:
    """Fige les lignes déjà calculées et marque la demande complète, None si introuvable.

    Idempotent sur le contenu : réémettre un devis dont les lignes et le total
    sont identiques renvoie celui déjà enregistré au lieu d'en créer un second.
    C'est indispensable côté Streamlit, qui rejoue tout le script à chaque
    interaction et rappellerait donc cette fonction sans que rien n'ait changé.
    Un besoin réellement modifié produit en revanche un nouveau devis : les
    lignes émises ne se réécrivent jamais (D11).
    """
    demande = session.scalar(
        select(Demande).where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
    )
    if demande is None:
        return None

    lignes = [asdict(ligne) for ligne in resultat.lignes]
    deja_emis = _retrouver_devis_identique(session, tenant_id, demande_id, lignes, resultat.total)
    if deja_emis is not None:
        return deja_emis

    devis = Devis(
        tenant_id=tenant_id,
        demande_id=demande_id,
        lignes=lignes,
        total=resultat.total,
    )
    session.add(devis)
    session.flush()
    recu = _recu(devis)
    # Passage à l'état complet par une requête filtrée sur le tenant autant que
    # sur l'identifiant, et non en mutant l'objet chargé : l'ORM n'écrirait
    # alors qu'un WHERE sur la clé primaire, et la règle du projet ne souffre
    # aucune exception (voir CLAUDE.md, Multi-locataires). Même transaction, donc
    # le devis et l'état de la demande sont validés d'un seul coup.
    session.execute(
        update(Demande)
        .where(Demande.id == demande_id, Demande.tenant_id == tenant_id)
        .values(etat=ETAT_COMPLETE)
    )
    session.commit()
    return recu


def _retrouver_devis_identique(
    session: Session, tenant_id: str, demande_id: str, lignes: list[dict], total: int
) -> DevisEmis | None:
    """Devis déjà émis pour cette demande avec ces lignes et ce total, sinon None.

    Comparaison sur le contenu plutôt que sur une empreinte stockée : les lignes
    figées sont déjà en base, elles font une clé d'idempotence sans colonne
    supplémentaire. Une demande n'en porte au pire que quelques-uns.
    """
    devis_de_la_demande = session.scalars(
        select(Devis).where(Devis.demande_id == demande_id, Devis.tenant_id == tenant_id)
    )
    for devis in devis_de_la_demande:
        if devis.lignes == lignes and devis.total == total:
            return _recu(devis)
    return None


def _recu(devis: Devis) -> DevisEmis:
    """Reçu détaché d'un devis en base, sûr à garder d'un rerun Streamlit à l'autre"""
    return DevisEmis(
        id=devis.id,
        total=devis.total,
        devise=devis.devise,
        date_emission=devis.date_emission,
    )
