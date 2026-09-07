"""Le hachage ne touche ni base ni réseau : ces tests sont purs (voir CONVENTIONS.md)"""
from src.auth.hachage import hash_mot_de_passe, verifie_mot_de_passe


def test_mot_de_passe_correct_est_verifie():
    hache = hash_mot_de_passe("Etoile-Demo-2026")

    assert verifie_mot_de_passe("Etoile-Demo-2026", hache)


def test_mot_de_passe_incorrect_est_refuse():
    hache = hash_mot_de_passe("Etoile-Demo-2026")

    assert not verifie_mot_de_passe("Autre-Mot-De-Passe", hache)


def test_mot_de_passe_avec_accents_est_verifie():
    hache = hash_mot_de_passe("Événement-Étoilé-2026")

    assert verifie_mot_de_passe("Événement-Étoilé-2026", hache)


def test_deux_hachages_du_meme_mot_de_passe_sont_differents():
    """Le sel est tiré au hasard à chaque appel : deux hachages d'un même mot
    de passe ne doivent jamais permettre de repérer deux comptes identiques."""
    premier_hache = hash_mot_de_passe("Etoile-Demo-2026")
    second_hache = hash_mot_de_passe("Etoile-Demo-2026")

    assert premier_hache != second_hache
    assert verifie_mot_de_passe("Etoile-Demo-2026", premier_hache)
    assert verifie_mot_de_passe("Etoile-Demo-2026", second_hache)


def test_hache_ne_contient_jamais_le_mot_de_passe_en_clair():
    mot_de_passe = "Etoile-Demo-2026"

    hache = hash_mot_de_passe(mot_de_passe)

    assert mot_de_passe not in hache


def test_hache_dun_algorithme_inconnu_est_refuse_sans_planter():
    """Un enregistrement corrompu ou produit par un ancien algorithme ne doit
    jamais faire planter la connexion, seulement la refuser."""
    hache = hash_mot_de_passe("Etoile-Demo-2026").replace("scrypt$", "md5$")

    assert not verifie_mot_de_passe("Etoile-Demo-2026", hache)
