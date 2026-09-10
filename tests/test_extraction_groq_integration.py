"""Appels réels à l'API Groq : exclus par défaut, lancer avec -m integration"""
import os
from datetime import date

import pytest

from src.extraction.groq import ExtracteurGroq
from src.extraction.types import Besoin
from src.orchestration.champs_obligatoires import identifier_champs_obligatoires_manquants

pytestmark = pytest.mark.integration

sans_cle_api = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY absente de l'environnement"
)


@sans_cle_api
def test_extraction_mariage_yaounde_300_invites_remplit_les_champs_principaux():
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "je veux organiser mon mariage à Yaoundé en juillet, on sera environ 300 personnes",
        Besoin(),
    )

    assert besoin.type_evenement is not None
    assert "mariage" in besoin.type_evenement.lower()
    assert besoin.ville is not None
    assert "yaound" in besoin.ville.lower()
    assert besoin.nombre_invites == 300


@sans_cle_api
def test_conversation_de_trois_messages_complete_le_besoin_obligatoire():
    """Le besoin se remplit au fil des messages, sans perdre l'acquis des tours précédents"""
    extracteur = ExtracteurGroq()
    besoin = Besoin()

    besoin = extracteur.extraire_besoin("Bonjour, je prépare un mariage", besoin)
    assert besoin.type_evenement is not None

    besoin = extracteur.extraire_besoin("nous serons 300 à Yaoundé, quartier Bastos", besoin)
    assert besoin.nombre_invites == 300
    assert besoin.quartier_souhaite is not None
    assert "bastos" in besoin.quartier_souhaite.lower()

    besoin = extracteur.extraire_besoin("le 12 décembre 2026, sur une seule journée", besoin)
    assert besoin.duree_jours == 1

    # Le tour précédent n'a effacé ni la ville ni le nombre d'invités
    assert besoin.nombre_invites == 300
    assert identifier_champs_obligatoires_manquants(besoin) == ()


@sans_cle_api
def test_quartier_seul_sans_ville_nommee_ne_remplit_pas_la_ville():
    """« Bastos » est un quartier de Yaoundé, pas une ville : il ne doit jamais se retrouver dans ville"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "Nous serons environ 300 personnes, pour un mariage du côté de Bastos", Besoin()
    )

    assert besoin.quartier_souhaite is not None
    assert "bastos" in besoin.quartier_souhaite.lower()
    assert besoin.ville is None


@sans_cle_api
def test_plage_de_dates_explicite_calcule_la_duree():
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin("Ce sera du 12 au 14 décembre 2026", Besoin())

    assert besoin.duree_jours == 3


@sans_cle_api
def test_date_seule_ne_fait_jamais_deviner_la_duree():
    """Non-régression de D21 : une date précise mais seule n'implique aucune durée"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin("Ce sera le 12 décembre 2026", Besoin())

    assert besoin.date_evenement is not None
    assert besoin.duree_jours is None


@sans_cle_api
def test_reformulation_reste_du_francais_lisible():
    extracteur = ExtracteurGroq()

    texte = extracteur.reformuler("Il me manque le nombre d'invités et la durée en jours.")

    assert isinstance(texte, str)
    assert texte.strip()


@sans_cle_api
def test_reformulation_dune_information_manquante_ninvente_jamais_de_chiffre():
    """Non-régression : le modèle a un jour répondu « 14 jours, du 5 au 19 juillet 2024 »
    à une phrase qui ne contenait aucun chiffre. Répété pour couvrir la variabilité du modèle."""
    extracteur = ExtracteurGroq()
    source = "Il me manque la durée en jours et la date."

    for _ in range(5):
        texte = extracteur.reformuler(source)
        assert not any(caractere.isdigit() for caractere in texte), (
            f"chiffre inventé dans la reformulation : {texte!r}"
        )


@sans_cle_api
def test_ville_du_cameroun_mal_orthographiee_est_reconnue():
    """Cas observé en test réel : le modèle butait sur les villes du pays"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "on fait ca a bafoussam, 200 personnes", Besoin(type_evenement="mariage")
    )

    assert besoin.ville == "Bafoussam"


@sans_cle_api
def test_vocabulaire_du_mariage_sans_le_mot_mariage():
    """« la dot » désigne un mariage coutumier : le type ne doit pas rester vide"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin("nous préparons la dot de ma fille", Besoin())

    assert besoin.type_evenement is not None
    assert "mariage" in besoin.type_evenement.lower()


@sans_cle_api
def test_une_journee_en_toutes_lettres_vaut_un_jour():
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "ce sera sur une seule journée", Besoin(type_evenement="mariage")
    )

    assert besoin.duree_jours == 1


@sans_cle_api
def test_ce_weekend_propose_deux_dates_sans_en_choisir_une():
    """Le modèle ne tranche pas entre samedi et dimanche : c'est au prospect (D40)"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "je veux organiser ça ce weekend", Besoin(type_evenement="mariage")
    )

    assert len(besoin.dates_possibles) >= 2
    assert all(len(date) == 10 for date in besoin.dates_possibles)


@sans_cle_api
def test_date_relative_dun_seul_jour_est_resolue_et_signalee_a_confirmer():
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "ce sera samedi prochain", Besoin(type_evenement="mariage")
    )

    assert besoin.date_evenement is not None
    assert "date_evenement" in besoin.champs_a_confirmer


@sans_cle_api
def test_dernier_samedi_de_decembre_tombe_bien_un_samedi():
    """Cas observé : le modèle proposait le jeudi 31 décembre, deux fois de suite"""
    extracteur = ExtracteurGroq()

    besoin = extracteur.extraire_besoin(
        "je veux me marier le dernier samedi de decembre", Besoin()
    )

    # Soit le modèle a produit un samedi, soit le garde-fou a écarté sa date :
    # dans les deux cas le prospect ne se voit jamais proposer un jeudi.
    if besoin.date_evenement is not None:
        assert date.fromisoformat(besoin.date_evenement).weekday() == 5
    else:
        assert besoin.champ_en_correction == "date_evenement"


@sans_cle_api
def test_prospect_qui_conteste_un_jour_ne_recoit_pas_la_meme_date():
    """« non samedi » après une proposition ne doit pas renvoyer le même jeudi"""
    extracteur = ExtracteurGroq()
    besoin_avant = Besoin(type_evenement="mariage", date_evenement="2026-12-31")

    besoin = extracteur.extraire_besoin("non samedi", besoin_avant)

    assert besoin.date_evenement != "2026-12-31"
