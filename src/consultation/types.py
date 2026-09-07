"""Vues du gestionnaire sur une demande, détachées de la session SQLAlchemy.

Le tableau de bord ne voit jamais un objet SQLAlchemy vivant : Streamlit rejoue
son script à chaque interaction, et un objet rattaché à une session refermée
lèverait DetachedInstanceError. Ces dataclasses figées portent exactement ce
que les écrans affichent, rien de plus.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProspectDeLaDemande:
    """Qui a demandé l'estimation, pour que le commercial puisse le rappeler (D26)"""

    nom: str
    telephone: str
    email: str | None
    consentement_contact: bool


@dataclass(frozen=True)
class LigneDevisFigee:
    """Une ligne de devis relue en base, telle qu'elle a été émise (D11)"""

    designation: str
    quantite: int
    prix_unitaire: int
    montant: int


@dataclass(frozen=True)
class DevisConsulte:
    """Un devis émis, avec ses lignes figées et son total"""

    id: str
    total: int
    devise: str
    date_emission: datetime
    lignes: tuple[LigneDevisFigee, ...]


@dataclass(frozen=True)
class LigneListeDemande:
    """Une demande telle que la liste du tableau de bord la présente.

    total_dernier_devis vaut None quand aucun devis n'a été émis : une
    conversation en cours n'a pas de montant, et afficher zéro laisserait
    croire à une estimation gratuite.
    """

    id: str
    date_creation: datetime
    etat: str
    canal: str
    type_evenement: str | None
    date_evenement: str | None
    ville: str | None
    quartier_souhaite: str | None
    nombre_invites: int | None
    prospect: ProspectDeLaDemande | None
    total_dernier_devis: int | None
    devise: str | None


@dataclass(frozen=True)
class DetailDemande:
    """Une demande, son besoin complet et les devis qui en sont sortis.

    devis est ordonné du plus récent au plus ancien : un besoin modifié après
    une première estimation en produit une seconde, sans réécrire la première.
    """

    resume: LigneListeDemande
    besoin: dict
    devis: tuple[DevisConsulte, ...]
