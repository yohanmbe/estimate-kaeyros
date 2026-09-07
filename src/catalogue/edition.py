"""Écriture du catalogue par le gestionnaire, symétrique de ressources.py (la lecture).

Le catalogue est la seule source des montants (D01) : ce qui s'écrit ici finit
dans un devis. La validation se fait donc à cette frontière, puisque les
colonnes categorie et unite_facturation sont des textes libres en base et
qu'aucune contrainte ne les protège (voir vocabulaire.py).

Retirer une prestation la désactive d'abord, sans la supprimer : elle
disparaît des options proposées au prospect mais reste modifiable ou
réactivable. La suppression définitive n'est possible qu'à partir d'une
prestation déjà retirée (voir supprimer_ressource) : Devis.lignes est un
instantané JSON figé à l'émission (désignation, prix, quantité, montant), pas
une clé étrangère vers ressource — un devis déjà émis reste donc lisible tel
quel après la suppression de la ressource qu'il citait (D11).
"""
from dataclasses import dataclass

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.catalogue.vocabulaire import CATEGORIES, UNITES_FACTURATION, champs_attributs
from src.db.models import Ressource


@dataclass(frozen=True)
class SaisieRessource:
    """Une prestation telle que le formulaire du tableau de bord la soumet"""

    nom: str
    categorie: str
    unite_facturation: str
    prix_unitaire: int
    attributs: dict


@dataclass(frozen=True)
class RessourceGestion:
    """Une prestation vue par le gestionnaire, retirées comprises.

    Différent de RessourceCatalogue, la vue du moteur : celle-ci porte l'état
    d'activation, que le gestionnaire doit voir et changer, et que le moteur
    n'a pas à connaître puisqu'il ne reçoit que les prestations actives.
    """

    id: str
    nom: str
    categorie: str
    unite_facturation: str
    prix_unitaire: int
    attributs: dict
    actif: bool


def valider_saisie(saisie: SaisieRessource) -> list[str]:
    """Liste des raisons de refuser la saisie, vide si elle est acceptable.

    Renvoie tous les problèmes d'un coup plutôt que le premier rencontré : le
    gestionnaire corrige son formulaire en une fois.
    """
    raisons = []
    if not saisie.nom.strip():
        raisons.append("Le nom de la prestation est obligatoire.")
    if saisie.categorie not in CATEGORIES:
        raisons.append(f"Catégorie inconnue : {saisie.categorie}.")
    if saisie.unite_facturation not in UNITES_FACTURATION:
        raisons.append(f"Unité de facturation inconnue : {saisie.unite_facturation}.")
    if saisie.prix_unitaire <= 0:
        raisons.append("Le prix unitaire doit être un entier de FCFA supérieur à zéro.")
    raisons.extend(_raisons_sur_les_attributs(saisie))
    return raisons


def lister_pour_gestion(
    session: Session, tenant_id: str, categorie: str | None = None
) -> list[RessourceGestion]:
    """Prestations du tenant, actives et retirées, triées par nom"""
    conditions = [Ressource.tenant_id == tenant_id]
    if categorie is not None:
        conditions.append(Ressource.categorie == categorie)
    ressources = session.scalars(
        select(Ressource).where(*conditions).order_by(Ressource.nom)
    )
    return [_convertir(ressource) for ressource in ressources]


def compter_ressources(session: Session, tenant_id: str) -> int:
    """Nombre de prestations du tenant : sert au repère de navigation"""
    return session.scalar(
        select(func.count(Ressource.id)).where(Ressource.tenant_id == tenant_id)
    )


def creer_ressource(session: Session, tenant_id: str, saisie: SaisieRessource) -> str:
    """Ajoute une prestation au catalogue du tenant et renvoie son identifiant"""
    _exiger_une_saisie_valide(saisie)
    ressource = Ressource(
        tenant_id=tenant_id,
        nom=saisie.nom.strip(),
        categorie=saisie.categorie,
        unite_facturation=saisie.unite_facturation,
        prix_unitaire=saisie.prix_unitaire,
        attributs=saisie.attributs,
    )
    session.add(ressource)
    # Identifiant lu après le flush et avant le commit, qui périmerait l'objet
    # et provoquerait une relecture sur la seule clé primaire, sans tenant_id.
    session.flush()
    identifiant = ressource.id
    session.commit()
    return identifiant


def modifier_ressource(
    session: Session, tenant_id: str, ressource_id: str, saisie: SaisieRessource
) -> bool:
    """Remplace les champs d'une prestation du tenant, False si elle est introuvable.

    Le filtre porte sur l'identifiant ET le tenant : les identifiants de
    ressources circulent dans les clés de widgets, connaître celui d'une autre
    entreprise ne doit rien permettre d'écrire chez elle.
    """
    _exiger_une_saisie_valide(saisie)
    resultat = session.execute(
        update(Ressource)
        .where(Ressource.id == ressource_id, Ressource.tenant_id == tenant_id)
        .values(
            nom=saisie.nom.strip(),
            categorie=saisie.categorie,
            unite_facturation=saisie.unite_facturation,
            prix_unitaire=saisie.prix_unitaire,
            attributs=saisie.attributs,
        )
    )
    session.commit()
    return resultat.rowcount == 1


def basculer_activation(session: Session, tenant_id: str, ressource_id: str) -> bool:
    """Retire du catalogue une prestation active, ou remet en service une retirée.

    Retirer ne supprime rien : la prestation disparaît des options proposées au
    prospect (charger_ressources_actives ne rend que les actives) mais reste
    référencée par les devis déjà émis.
    """
    ressource = session.scalar(
        select(Ressource).where(
            Ressource.id == ressource_id, Ressource.tenant_id == tenant_id
        )
    )
    if ressource is None:
        return False
    resultat = session.execute(
        update(Ressource)
        .where(Ressource.id == ressource_id, Ressource.tenant_id == tenant_id)
        .values(actif=not ressource.actif)
    )
    session.commit()
    return resultat.rowcount == 1


def supprimer_ressource(session: Session, tenant_id: str, ressource_id: str) -> bool:
    """Supprime définitivement une prestation déjà retirée du tenant.

    Refuse une prestation encore active : la suppression n'est proposée à
    l'écran que depuis le bloc des prestations retirées, et cette même règle
    est vérifiée ici pour qu'un identifiant actif deviné dans une clé de
    widget ne puisse pas faire disparaître une prestation encore proposée.
    """
    resultat = session.execute(
        delete(Ressource).where(
            Ressource.id == ressource_id,
            Ressource.tenant_id == tenant_id,
            Ressource.actif.is_(False),
        )
    )
    session.commit()
    return resultat.rowcount == 1


def _exiger_une_saisie_valide(saisie: SaisieRessource) -> None:
    """Refuse d'écrire une saisie invalide, même si l'écran a oublié de la vérifier"""
    raisons = valider_saisie(saisie)
    if raisons:
        raise ValueError(" ".join(raisons))


def _raisons_sur_les_attributs(saisie: SaisieRessource) -> list[str]:
    """Vérifie les attributs attendus pour la catégorie (voir SCHEMA_ATTRIBUTS)"""
    raisons = []
    for champ in champs_attributs(saisie.categorie):
        valeur = saisie.attributs.get(champ.cle)
        manquant = valeur is None or (isinstance(valeur, str) and not valeur.strip())
        if champ.obligatoire and manquant:
            raisons.append(f"{champ.libelle} est obligatoire pour cette catégorie.")
            continue
        if manquant:
            continue
        if champ.nature == "entier" and (not isinstance(valeur, int) or valeur <= 0):
            raisons.append(f"{champ.libelle} doit être un entier supérieur à zéro.")
    return raisons


def _convertir(ressource: Ressource) -> RessourceGestion:
    """Traduit une ligne de la table ressource vers la vue du gestionnaire"""
    return RessourceGestion(
        id=ressource.id,
        nom=ressource.nom,
        categorie=ressource.categorie,
        unite_facturation=ressource.unite_facturation,
        prix_unitaire=ressource.prix_unitaire,
        attributs=ressource.attributs,
        actif=ressource.actif,
    )
