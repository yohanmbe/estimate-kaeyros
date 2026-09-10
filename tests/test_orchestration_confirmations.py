"""Hypothèses de l'extracteur soumises au prospect, sans LLM ni base"""
from src.extraction.types import Besoin
from src.orchestration.confirmations import (
    identifier_champ_en_correction,
    identifier_hypothese_a_confirmer,
    reporter_choix_du_prospect,
)
from src.orchestration.questions import formuler_question_confirmation


def test_besoin_sans_hypothese_na_rien_a_faire_confirmer():
    assert identifier_hypothese_a_confirmer(Besoin(type_evenement="mariage")) is None


def test_type_devenement_deduit_est_a_confirmer():
    besoin = Besoin(type_evenement="mariage", champs_a_confirmer=("type_evenement",))

    assert identifier_hypothese_a_confirmer(besoin) == ("type_evenement", ("mariage",))


def test_hypothese_deja_confirmee_ne_revient_plus():
    besoin = Besoin(
        type_evenement="mariage",
        champs_a_confirmer=("type_evenement",),
        champs_confirmes=("type_evenement",),
    )

    assert identifier_hypothese_a_confirmer(besoin) is None


def test_champ_signale_mais_resté_vide_nest_pas_propose():
    """Rien à confirmer tant qu'il n'y a pas de valeur : c'est une question de besoin, pas de doute"""
    besoin = Besoin(champs_a_confirmer=("ville",))

    assert identifier_hypothese_a_confirmer(besoin) is None


def test_ce_weekend_propose_le_samedi_et_le_dimanche():
    besoin = Besoin(dates_possibles=("2026-09-12", "2026-09-13"))

    assert identifier_hypothese_a_confirmer(besoin) == (
        "date_evenement",
        ("2026-09-12", "2026-09-13"),
    )


def test_date_tranchee_par_le_prospect_ne_revient_plus():
    besoin = Besoin(
        date_evenement="2026-09-12",
        dates_possibles=("2026-09-12", "2026-09-13"),
        champs_confirmes=("date_evenement",),
    )

    assert identifier_hypothese_a_confirmer(besoin) is None


def test_les_dates_possibles_passent_avant_les_autres_hypotheses():
    besoin = Besoin(
        type_evenement="mariage",
        champs_a_confirmer=("type_evenement",),
        dates_possibles=("2026-09-12", "2026-09-13"),
    )

    champ, _ = identifier_hypothese_a_confirmer(besoin)
    assert champ == "date_evenement"


def test_question_sur_une_seule_valeur_demande_confirmation():
    question = formuler_question_confirmation("type_evenement", ("mariage",))

    assert question == "Votre événement est bien un mariage ?"


def test_question_sur_une_date_ecrit_la_date_en_toutes_lettres():
    question = formuler_question_confirmation("date_evenement", ("2026-09-12",))

    assert question == "Votre événement a bien lieu le samedi 12 septembre 2026 ?"


def test_question_sur_deux_dates_fait_choisir_entre_elles():
    question = formuler_question_confirmation(
        "date_evenement", ("2026-09-12", "2026-09-13")
    )

    assert question == (
        "Quelle date retenez-vous : samedi 12 septembre 2026 ou dimanche 13 septembre 2026 ?"
    )


def test_date_restee_hors_format_est_montree_dans_les_mots_du_prospect():
    question = formuler_question_confirmation("date_evenement", ("mi-décembre",))

    assert question == "Votre événement a bien lieu le mi-décembre ?"


def test_champ_corrige_est_le_seul_redemande():
    """« Ce n'est pas la date » ne doit pas déclencher une question sur autre chose"""
    besoin = Besoin(
        type_evenement="mariage",
        champs_a_confirmer=("type_evenement",),
        champ_en_correction="date_evenement",
    )

    assert identifier_champ_en_correction(besoin) == "date_evenement"


def test_correction_close_des_que_le_champ_est_redonne():
    besoin = Besoin(date_evenement="2026-12-26", champ_en_correction="date_evenement")

    assert identifier_champ_en_correction(besoin) is None


def test_besoin_sans_correction_en_cours_ne_bloque_rien():
    assert identifier_champ_en_correction(Besoin(type_evenement="mariage")) is None


def test_correction_en_cours_survit_a_un_message_qui_ny_repond_pas():
    besoin_avant = Besoin(champ_en_correction="date_evenement")
    besoin_extrait = Besoin(ville="Yaoundé")

    resultat = reporter_choix_du_prospect(besoin_extrait, besoin_avant)

    assert resultat.champ_en_correction == "date_evenement"


def test_correction_se_referme_quand_le_message_donne_la_valeur():
    besoin_avant = Besoin(champ_en_correction="date_evenement")
    besoin_extrait = Besoin(date_evenement="2026-12-26")

    resultat = reporter_choix_du_prospect(besoin_extrait, besoin_avant)

    assert resultat.champ_en_correction is None


def test_demandes_sur_mesure_survivent_a_une_extraction():
    """Elles viennent d'un bouton : le modèle ne les connaît pas et les effacerait"""
    besoin_avant = Besoin(categories_sur_mesure=("salle",))

    resultat = reporter_choix_du_prospect(Besoin(ville="Yaoundé"), besoin_avant)

    assert resultat.categories_sur_mesure == ("salle",)
