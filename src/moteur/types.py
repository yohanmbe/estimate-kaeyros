"""Structures de données du moteur de devis, indépendantes de SQLAlchemy et du LLM"""
from dataclasses import dataclass
from typing import Literal

BaseQuantite = Literal["invite", "jour", "forfait"]


@dataclass(frozen=True)
class RessourceCatalogue:
    """Vue du moteur sur une ressource du catalogue"""

    id: str
    nom: str
    categorie: str
    unite_facturation: str
    prix_unitaire: int
    attributs: dict


@dataclass(frozen=True)
class RegleQuantite:
    """Une entrée de lignes_par_defaut d'un modele_evenement"""

    categorie: str
    base: BaseQuantite
    multiplicateur: int = 1


@dataclass(frozen=True)
class BesoinChiffrage:
    """Sous-ensemble de Demande.besoin nécessaire au calcul du devis.

    Ces champs sont garantis présents par l'orchestrateur avant le passage
    au chiffrage : le moteur ne leur applique aucune valeur par défaut.
    """

    nombre_invites: int
    duree_jours: int
    quartier_souhaite: str
    budget_declare: int | None


@dataclass(frozen=True)
class LigneDevis:
    """Une ligne du devis, prête à être enregistrée dans Devis.lignes"""

    designation: str
    quantite: int
    prix_unitaire: int
    montant: int
    ressource_id: str


@dataclass(frozen=True)
class CategorieNonSatisfaite:
    """Une catégorie attendue par le modèle sans ressource disponible"""

    categorie: str


@dataclass(frozen=True)
class ResultatChiffrage:
    """Le résultat complet du calcul d'un devis"""

    lignes: list[LigneDevis]
    total: int
    categories_non_satisfaites: list[CategorieNonSatisfaite]
    depasse_budget: bool | None
