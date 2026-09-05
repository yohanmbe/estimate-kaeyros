"""Interface abstraite de la couche LLM (voir ARCHITECTURE.md, section Couche LLM)

Tous les appels au LLM passent par cette interface. Le fournisseur reste
caché derrière : changer de fournisseur revient à écrire une nouvelle
implémentation, sans toucher à l'orchestrateur ni au moteur de devis.
"""
from abc import ABC, abstractmethod

from src.extraction.types import Besoin


class InterfaceLLM(ABC):
    """Les deux seules actions confiées au LLM : extraire, reformuler.

    Aucune méthode ne renvoie de montant ni de décision de conversation :
    ce n'est pas le rôle du LLM (voir D01).
    """

    @abstractmethod
    def extraire_besoin(self, message: str, besoin_actuel: Besoin) -> Besoin:
        """Met à jour le besoin structuré à partir d'un nouveau message du prospect"""

    @abstractmethod
    def reformuler(self, contenu: str) -> str:
        """Reformule un contenu en français naturel, sans en changer le sens"""
