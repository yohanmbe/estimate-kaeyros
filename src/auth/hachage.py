"""Hachage et vérification des mots de passe, via hashlib (stdlib).

Pas de dépendance externe (bcrypt/argon2-cffi) : scrypt est fourni par la
stdlib Python depuis la 3.6 et convient au hachage de mots de passe grâce à
son facteur de coût réglable.
"""
import hashlib
import hmac
import os

_N = 2**14
_R = 8
_P = 1
_TAILLE_SEL = 16
_TAILLE_HACHE = 32


def hash_mot_de_passe(mot_de_passe: str) -> str:
    """Dérive un mot de passe en clair vers une chaîne à stocker en base.

    Le sel et les paramètres scrypt sont encodés dans la chaîne retournée,
    pour que la vérification n'ait pas besoin de les connaître à l'avance.
    """
    sel = os.urandom(_TAILLE_SEL)
    hache = hashlib.scrypt(
        mot_de_passe.encode("utf-8"), salt=sel, n=_N, r=_R, p=_P, dklen=_TAILLE_HACHE
    )
    return f"scrypt${_N}${_R}${_P}${sel.hex()}${hache.hex()}"


def verifie_mot_de_passe(mot_de_passe: str, hache: str) -> bool:
    """Vérifie un mot de passe en clair contre une chaîne produite par hash_mot_de_passe"""
    algorithme, n, r, p, sel_hex, hache_hex = hache.split("$")
    if algorithme != "scrypt":
        return False
    sel = bytes.fromhex(sel_hex)
    hache_attendu = bytes.fromhex(hache_hex)
    hache_calcule = hashlib.scrypt(
        mot_de_passe.encode("utf-8"),
        salt=sel,
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=len(hache_attendu),
    )
    return hmac.compare_digest(hache_calcule, hache_attendu)
