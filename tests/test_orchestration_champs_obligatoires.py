from src.extraction.types import Besoin
from src.orchestration.champs_obligatoires import identifier_champs_obligatoires_manquants


def test_besoin_vide_manque_les_cinq_champs_dans_l_ordre_de_priorite():
    resultat = identifier_champs_obligatoires_manquants(Besoin())

    assert resultat == (
        "type_evenement",
        "nombre_invites",
        "duree_jours",
        "ville",
        "date_evenement",
    )


def test_besoin_complet_ne_manque_aucun_champ():
    besoin = Besoin(
        type_evenement="mariage",
        nombre_invites=300,
        duree_jours=2,
        ville="Yaounde",
        date_evenement="2026-07-12",
    )

    resultat = identifier_champs_obligatoires_manquants(besoin)

    assert resultat == ()


def test_quartier_absent_ne_compte_jamais_comme_manquant():
    besoin = Besoin(
        type_evenement="mariage",
        nombre_invites=300,
        duree_jours=2,
        ville="Yaounde",
        date_evenement="2026-07-12",
        quartier_souhaite=None,
    )

    resultat = identifier_champs_obligatoires_manquants(besoin)

    assert resultat == ()


def test_seuls_les_champs_encore_absents_sont_renvoyes_dans_l_ordre():
    besoin = Besoin(type_evenement="mariage", ville="Yaounde")

    resultat = identifier_champs_obligatoires_manquants(besoin)

    assert resultat == ("nombre_invites", "duree_jours", "date_evenement")
