from src.presentation.montant import ESPACE_INSECABLE, formater_montant, formater_nombre


def test_montant_porte_toujours_sa_devise():
    assert formater_montant(450_000).endswith("FCFA")


def test_montant_de_plusieurs_millions_separe_ses_milliers():
    attendu = ESPACE_INSECABLE.join(["2", "850", "000"]) + ESPACE_INSECABLE + "FCFA"

    assert formater_montant(2_850_000) == attendu


def test_montant_sous_le_millier_na_aucun_separateur():
    assert formater_montant(500) == "500" + ESPACE_INSECABLE + "FCFA"


def test_montant_nul_saffiche_zero_plutot_que_vide():
    assert formater_montant(0) == "0" + ESPACE_INSECABLE + "FCFA"


def test_separateur_est_un_espace_insecable_jamais_un_espace_ordinaire():
    """Un total ne doit jamais se couper en fin de ligne, ni avant sa devise.

    L'espace ordinaire est vérifié explicitement : c'est la régression probable
    si quelqu'un réécrit le formatage sans lire le commentaire du module.
    """
    assert ESPACE_INSECABLE == chr(160)
    assert " " not in formater_montant(2_850_000)


def test_nombre_dinvites_est_separe_mais_sans_devise():
    assert formater_nombre(1_200) == "1" + ESPACE_INSECABLE + "200"
    assert "FCFA" not in formater_nombre(1_200)
