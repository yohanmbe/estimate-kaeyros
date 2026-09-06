import os

import pytest

from src.extraction.mistral import ExtracteurMistral
from src.extraction.types import Besoin

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.getenv("MISTRAL_API_KEY"), reason="MISTRAL_API_KEY absente de l'environnement")
def test_extraction_mariage_yaounde_300_invites_remplit_les_champs_principaux():
    extracteur = ExtracteurMistral()

    besoin = extracteur.extraire_besoin(
        "je veux organiser mon mariage à Yaoundé en juillet, on sera environ 300 personnes",
        Besoin(),
    )

    assert besoin.type_evenement is not None
    assert "mariage" in besoin.type_evenement.lower()
    assert besoin.ville is not None
    assert "yaound" in besoin.ville.lower()
    assert besoin.nombre_invites == 300
