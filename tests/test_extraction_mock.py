from src.extraction.mock import ExtracteurMock
from src.extraction.types import Besoin


def test_extracteur_mock_sans_reponse_configuree_renvoie_le_besoin_actuel():
    besoin_actuel = Besoin(type_evenement="mariage", nombre_invites=300)
    extracteur = ExtracteurMock()

    besoin_mis_a_jour = extracteur.extraire_besoin("300 invités à Bastos", besoin_actuel)

    assert besoin_mis_a_jour == besoin_actuel
    assert extracteur.messages_recus == ["300 invités à Bastos"]


def test_extracteur_mock_renvoie_les_besoins_configures_dans_lordre():
    premier_besoin = Besoin(type_evenement="mariage")
    second_besoin = Besoin(type_evenement="mariage", ville="Yaounde")
    extracteur = ExtracteurMock(besoins_a_renvoyer=[premier_besoin, second_besoin])

    assert extracteur.extraire_besoin("un mariage", Besoin()) == premier_besoin
    assert extracteur.extraire_besoin("a Yaounde", premier_besoin) == second_besoin


def test_extracteur_mock_reformuler_renvoie_le_texte_configure():
    extracteur = ExtracteurMock(textes_a_renvoyer=["Combien d'invités attendez-vous ?"])

    texte = extracteur.reformuler("nombre_invites manquant")

    assert texte == "Combien d'invités attendez-vous ?"
    assert extracteur.contenus_recus == ["nombre_invites manquant"]
