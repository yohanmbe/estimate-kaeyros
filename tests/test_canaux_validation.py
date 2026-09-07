from src.canaux.validation import email_valide, telephone_valide


def test_telephone_avec_indicatif_et_neuf_chiffres_est_valide():
    assert telephone_valide("+237690000000") is True


def test_telephone_sans_indicatif_est_valide():
    assert telephone_valide("690000000") is True


def test_telephone_avec_espaces_et_tirets_est_valide():
    assert telephone_valide("+237 690-00-00-00") is True


def test_telephone_avec_lettres_est_refuse():
    assert telephone_valide("appelez-moi") is False


def test_telephone_trop_court_est_refuse():
    assert telephone_valide("1234") is False


def test_telephone_vide_est_refuse():
    assert telephone_valide("") is False


def test_email_bien_forme_est_valide():
    assert email_valide("awa.ngo@example.com") is True


def test_email_sans_arobase_est_refuse():
    assert email_valide("awa.ngo-example.com") is False


def test_email_sans_domaine_est_refuse():
    assert email_valide("awa.ngo@") is False
