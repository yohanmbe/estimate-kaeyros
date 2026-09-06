"""Fonctions pures de groq.py, sans appel réseau (voir test_extraction_groq_integration.py pour le reste)"""
from src.extraction.groq import _contient_un_nombre_invente


def test_reformulation_sans_aucun_nombre_est_acceptee():
    source = "Il me manque la durée en jours et la date."
    reformule = "Il me faut encore connaître la durée en jours et la date de l'événement."

    assert _contient_un_nombre_invente(source, reformule) is False


def test_reformulation_inventant_une_duree_et_une_annee_est_detectee():
    """Reproduit le cas observé : le modèle invente « 14 jours » et « 2024 » à partir de rien"""
    source = "Il me manque la durée en jours et la date."
    reformule = "La durée totale est de 14 jours, du 5 juillet au 19 juillet 2024."

    assert _contient_un_nombre_invente(source, reformule) is True


def test_nombre_deja_present_dans_la_source_nest_pas_signale():
    source = "Il reste 300 invités à confirmer."
    reformule = "Il vous reste 300 invités à confirmer."

    assert _contient_un_nombre_invente(source, reformule) is False
