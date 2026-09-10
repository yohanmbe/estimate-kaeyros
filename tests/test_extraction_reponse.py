"""Validation et normalisation de la réponse du modèle, sans appel réseau

Voir test_extraction_groq_integration.py pour les cas de langage réel.
"""
import json

from src.extraction.reponse import contient_un_nombre_invente, parser_besoin


def reponse_modele(**champs) -> str:
    """Fabrique la réponse JSON que le modèle est censé renvoyer"""
    return json.dumps(champs, ensure_ascii=False)


def test_reformulation_sans_aucun_nombre_est_acceptee():
    source = "Il me manque la durée en jours et la date."
    reformule = "Il me faut encore connaître la durée en jours et la date de l'événement."

    assert contient_un_nombre_invente(source, reformule) is False


def test_reformulation_inventant_une_duree_et_une_annee_est_detectee():
    """Reproduit le cas observé : le modèle invente « 14 jours » et « 2024 » à partir de rien"""
    source = "Il me manque la durée en jours et la date."
    reformule = "La durée totale est de 14 jours, du 5 juillet au 19 juillet 2024."

    assert contient_un_nombre_invente(source, reformule) is True


def test_nombre_deja_present_dans_la_source_nest_pas_signale():
    source = "Il reste 300 invités à confirmer."
    reformule = "Il vous reste 300 invités à confirmer."

    assert contient_un_nombre_invente(source, reformule) is False


def test_ville_mal_orthographiee_par_le_modele_est_normalisee():
    besoin = parser_besoin(reponse_modele(ville="yaounde"))

    assert besoin is not None
    assert besoin.ville == "Yaoundé"


def test_espaces_superflus_sont_retires_des_champs_texte():
    besoin = parser_besoin(reponse_modele(type_evenement="  mariage  ", quartier_souhaite=" Bastos "))

    assert besoin is not None
    assert besoin.type_evenement == "mariage"
    assert besoin.quartier_souhaite == "Bastos"


def test_champ_texte_vide_est_traite_comme_une_absence():
    besoin = parser_besoin(reponse_modele(type_evenement="", ville="   "))

    assert besoin is not None
    assert besoin.type_evenement is None
    assert besoin.ville is None


def test_date_au_format_canonique_na_rien_a_confirmer():
    besoin = parser_besoin(reponse_modele(date_evenement="2026-12-12"))

    assert besoin is not None
    assert besoin.date_evenement == "2026-12-12"
    assert besoin.champs_a_confirmer == ()


def test_date_hors_format_est_conservee_et_part_a_confirmer():
    """La perdre en silence reviendrait à la redemander comme si le prospect n'avait rien dit"""
    besoin = parser_besoin(reponse_modele(date_evenement="mi-décembre"))

    assert besoin is not None
    assert besoin.date_evenement == "mi-décembre"
    assert besoin.champs_a_confirmer == ("date_evenement",)


def test_date_inexistante_au_calendrier_part_aussi_a_confirmer():
    besoin = parser_besoin(reponse_modele(date_evenement="2026-02-30"))

    assert besoin is not None
    assert besoin.date_evenement == "2026-02-30"
    assert besoin.champs_a_confirmer == ("date_evenement",)


def test_hypothese_signalee_par_le_modele_est_conservee():
    besoin = parser_besoin(
        reponse_modele(type_evenement="mariage", champs_a_confirmer=["type_evenement"])
    )

    assert besoin is not None
    assert besoin.champs_a_confirmer == ("type_evenement",)


def test_nom_de_champ_inconnu_signale_par_le_modele_est_ignore():
    besoin = parser_besoin(reponse_modele(champs_a_confirmer=["couleur_des_nappes"]))

    assert besoin is not None
    assert besoin.champs_a_confirmer == ()


def test_date_hors_format_deja_signalee_nest_pas_comptee_deux_fois():
    besoin = parser_besoin(
        reponse_modele(date_evenement="ce weekend", champs_a_confirmer=["date_evenement"])
    )

    assert besoin is not None
    assert besoin.champs_a_confirmer == ("date_evenement",)


def test_dates_possibles_dun_weekend_sont_conservees():
    besoin = parser_besoin(reponse_modele(dates_possibles=["2026-09-12", "2026-09-13"]))

    assert besoin is not None
    assert besoin.dates_possibles == ("2026-09-12", "2026-09-13")
    assert besoin.date_evenement is None


def test_reponse_qui_nest_pas_du_json_est_rejetee():
    assert parser_besoin("désolé, je n'ai pas compris") is None


def test_reponse_dont_un_entier_arrive_en_texte_est_rejetee():
    assert parser_besoin(reponse_modele(nombre_invites="300")) is None


def test_reponse_dont_un_booleen_remplace_un_entier_est_rejetee():
    assert parser_besoin(reponse_modele(duree_jours=True)) is None


def test_date_tombant_un_autre_jour_que_celui_nomme_est_ecartee():
    """« Le dernier samedi de décembre » avait produit un jeudi, proposé deux fois"""
    besoin = parser_besoin(
        reponse_modele(date_evenement="2026-12-31"),
        message="je veux me marier le dernier samedi de decembre",
    )

    assert besoin is not None
    assert besoin.date_evenement is None
    assert besoin.champ_en_correction == "date_evenement"


def test_date_tombant_le_jour_nomme_est_conservee():
    besoin = parser_besoin(
        reponse_modele(date_evenement="2026-12-26"),
        message="le dernier samedi de decembre",
    )

    assert besoin is not None
    assert besoin.date_evenement == "2026-12-26"
    assert besoin.champ_en_correction is None


def test_message_citant_deux_jours_ne_declenche_aucune_correction():
    """« Samedi ou dimanche » n'est pas tranchable : on ne choisit pas à sa place"""
    besoin = parser_besoin(
        reponse_modele(date_evenement="2026-09-13"),
        message="samedi ou dimanche, peu importe",
    )

    assert besoin is not None
    assert besoin.date_evenement == "2026-09-13"


def test_message_sans_jour_nomme_laisse_la_date_tranquille():
    besoin = parser_besoin(
        reponse_modele(date_evenement="2026-12-31"), message="le 31 decembre"
    )

    assert besoin is not None
    assert besoin.date_evenement == "2026-12-31"


def test_mot_contenant_un_nom_de_jour_ne_compte_pas():
    """« mardi » ne doit pas être vu dans « mardigras » : on cherche des mots entiers"""
    besoin = parser_besoin(
        reponse_modele(date_evenement="2026-12-31"), message="pour le mardigras"
    )

    assert besoin is not None
    assert besoin.date_evenement == "2026-12-31"
