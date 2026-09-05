"""Implémentation mock de InterfaceLLM, sans appel à un service externe

Les réponses sont fournies à l'avance par l'appelant (typiquement un test)
et renvoyées dans l'ordre de leur consommation.
"""
from src.extraction.interface import InterfaceLLM
from src.extraction.types import Besoin


class ExtracteurMock(InterfaceLLM):
    """Renvoie des réponses prédéfinies, contrôlées par les tests"""

    def __init__(
        self,
        besoins_a_renvoyer: list[Besoin] | None = None,
        textes_a_renvoyer: list[str] | None = None,
    ) -> None:
        self._besoins_a_renvoyer = list(besoins_a_renvoyer or [])
        self._textes_a_renvoyer = list(textes_a_renvoyer or [])
        self.messages_recus: list[str] = []
        self.contenus_recus: list[str] = []

    def extraire_besoin(self, message: str, besoin_actuel: Besoin) -> Besoin:
        """Enregistre le message reçu et renvoie le prochain besoin prédéfini"""
        self.messages_recus.append(message)
        if not self._besoins_a_renvoyer:
            return besoin_actuel
        return self._besoins_a_renvoyer.pop(0)

    def reformuler(self, contenu: str) -> str:
        """Enregistre le contenu reçu et renvoie le prochain texte prédéfini"""
        self.contenus_recus.append(contenu)
        if not self._textes_a_renvoyer:
            return contenu
        return self._textes_a_renvoyer.pop(0)
