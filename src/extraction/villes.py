"""Villes du Cameroun et normalisation de leur graphie

Le prospect écrit « yaounde », « Yaoundé » ou « YAOUNDE » pour la même ville.
Sans normalisation, ces trois graphies sont trois valeurs différentes dans le
besoin, et le gestionnaire retrouve trois villes dans son tableau de bord.

Le Cameroun est le socle, pas une liste fermée : une ville absente de cette
liste est conservée telle que le prospect l'a écrite, jamais effacée.
"""
import unicodedata

VILLES_CAMEROUN: tuple[str, ...] = (
    # Centre
    "Yaoundé", "Mbalmayo", "Obala", "Bafia", "Nanga-Eboko", "Akonolinga",
    "Mfou", "Ntui", "Monatélé", "Eséka",
    # Littoral
    "Douala", "Nkongsamba", "Edéa", "Loum", "Manjo", "Mbanga", "Yabassi",
    "Dizangué", "Penja",
    # Ouest
    "Bafoussam", "Dschang", "Mbouda", "Bafang", "Foumban", "Foumbot",
    "Bangangté", "Baham", "Bandjoun",
    # Nord-Ouest
    "Bamenda", "Kumbo", "Wum", "Ndop", "Nkambé", "Batibo", "Mbengwi", "Fundong",
    # Sud-Ouest
    "Buéa", "Limbé", "Kumba", "Tiko", "Mamfé", "Muyuka", "Mutengene", "Bangem",
    # Nord
    "Garoua", "Guider", "Figuil", "Poli", "Lagdo", "Tcholliré",
    # Extrême-Nord
    "Maroua", "Kousséri", "Mokolo", "Yagoua", "Kaélé", "Mora", "Waza",
    # Adamaoua
    "Ngaoundéré", "Meiganga", "Tibati", "Banyo", "Tignère",
    # Est
    "Bertoua", "Batouri", "Abong-Mbang", "Yokadouma", "Garoua-Boulaï", "Bélabo",
    # Sud
    "Ebolowa", "Kribi", "Sangmélima", "Ambam", "Djoum", "Campo", "Mvangan",
)


def _aplatir(texte: str) -> str:
    """Réduit un nom à sa forme comparable : sans accents, sans casse, sans tiret"""
    sans_accents = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texte)
        if unicodedata.category(caractere) != "Mn"
    )
    return sans_accents.casefold().replace("-", " ").strip()


_VILLES_PAR_FORME_APLATIE = {_aplatir(ville): ville for ville in VILLES_CAMEROUN}


def normaliser_ville(texte: str | None) -> str | None:
    """Renvoie la graphie canonique d'une ville connue, sinon le texte reçu nettoyé.

    Une ville hors du Cameroun n'est ni corrigée ni supprimée : le produit ne
    prétend pas connaître toutes les villes du monde, il refuse simplement de
    perdre ce que le prospect a dit.
    """
    if texte is None:
        return None
    nettoye = texte.strip()
    if not nettoye:
        return None
    return _VILLES_PAR_FORME_APLATIE.get(_aplatir(nettoye), nettoye)
