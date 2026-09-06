"""Accès en lecture au catalogue d'un tenant, converti vers les types du moteur

Toute requête filtre sur tenant_id : un catalogue n'est jamais partagé entre
deux entreprises clientes (voir D05). Le moteur ne voit jamais un objet
SQLAlchemy, seulement des dataclasses détachées de la session.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import ModeleEvenement, Ressource
from src.moteur.types import BaseQuantite, RegleQuantite, RessourceCatalogue

# lignes_par_defaut décrit la base de calcul avec le vocabulaire du besoin
# (voir data/seed/seed.py) ; le moteur, lui, raisonne en invite/jour/forfait.
BASES_DE_CALCUL: dict[str, BaseQuantite] = {
    "nombre_invites": "invite",
    "duree_jours": "jour",
    "forfait": "forfait",
}


def charger_ressources_actives(session: Session, tenant_id: str) -> list[RessourceCatalogue]:
    """Charge les ressources actives du tenant, telles que le moteur les voit"""
    ressources = session.scalars(
        select(Ressource)
        .where(Ressource.tenant_id == tenant_id, Ressource.actif.is_(True))
        .order_by(Ressource.nom)
    )
    return [_convertir_ressource(ressource) for ressource in ressources]


def charger_modele_evenement(
    session: Session, tenant_id: str, nom: str
) -> list[RegleQuantite] | None:
    """Charge les règles de quantité du modèle nommé, None si le tenant n'en a pas.

    L'absence de modèle est signalée plutôt que remplacée par une liste vide :
    un modèle vide produirait un devis à zéro franc, c'est à dire un montant
    faux présenté comme un montant calculé.
    """
    modele = session.scalar(
        select(ModeleEvenement).where(
            ModeleEvenement.tenant_id == tenant_id, ModeleEvenement.nom == nom
        )
    )
    if modele is None:
        return None
    return [_convertir_regle(regle) for regle in modele.lignes_par_defaut]


def _convertir_ressource(ressource: Ressource) -> RessourceCatalogue:
    """Traduit une ligne de la table ressource vers la vue du moteur"""
    return RessourceCatalogue(
        id=ressource.id,
        nom=ressource.nom,
        categorie=ressource.categorie,
        unite_facturation=ressource.unite_facturation,
        prix_unitaire=ressource.prix_unitaire,
        attributs=ressource.attributs,
    )


def _convertir_regle(regle: dict) -> RegleQuantite:
    """Traduit une entrée de lignes_par_defaut vers une règle de quantité"""
    base = BASES_DE_CALCUL.get(regle["base_calcul"])
    if base is None:
        raise ValueError(f"base_calcul inconnue dans lignes_par_defaut : {regle['base_calcul']}")
    return RegleQuantite(
        categorie=regle["categorie"],
        base=base,
        multiplicateur=regle["quantite_par_unite"],
    )
