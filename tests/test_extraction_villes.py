"""Normalisation des villes, sans appel LLM"""
from src.extraction.villes import VILLES_CAMEROUN, normaliser_ville


def test_ville_sans_accent_ni_majuscule_retrouve_sa_graphie_officielle():
    assert normaliser_ville("yaounde") == "Yaoundé"
    assert normaliser_ville("YAOUNDE") == "Yaoundé"
    assert normaliser_ville("Yaounde") == "Yaoundé"


def test_ville_deja_bien_ecrite_reste_identique():
    assert normaliser_ville("Douala") == "Douala"


def test_ville_avec_espaces_superflus_est_nettoyee():
    assert normaliser_ville("  Bafoussam  ") == "Bafoussam"


def test_ville_ecrite_avec_un_tiret_ou_un_espace_designe_la_meme_ville():
    assert normaliser_ville("nanga eboko") == "Nanga-Eboko"
    assert normaliser_ville("Nanga-Eboko") == "Nanga-Eboko"


def test_ville_hors_du_cameroun_est_conservee_telle_quelle():
    """Le Cameroun est le socle, pas une liste fermée : on ne perd rien"""
    assert normaliser_ville("Libreville") == "Libreville"
    assert normaliser_ville("Paris") == "Paris"


def test_absence_de_ville_reste_une_absence():
    assert normaliser_ville(None) is None
    assert normaliser_ville("") is None
    assert normaliser_ville("   ") is None


def test_les_grandes_villes_du_cameroun_sont_connues():
    for ville in ("Yaoundé", "Douala", "Bafoussam", "Bamenda", "Garoua", "Maroua",
                  "Ngaoundéré", "Bertoua", "Ebolowa", "Kribi", "Buéa", "Limbé"):
        assert ville in VILLES_CAMEROUN
