"""Sélection des ressources candidates pour une catégorie du devis"""
from src.moteur.types import BesoinChiffrage, RegleQuantite, RessourceCatalogue

NOMBRE_MAX_OPTIONS_PAR_CATEGORIE = 3

CATEGORIE_SALLE = "salle"

# Au-delà de ce rapport, une salle est trop grande pour l'événement : 150
# places pour 20 invités, ce n'est plus une salle qui convient, c'est la
# seule que le catalogue sache proposer. On la montre quand même, avec le
# devis sur mesure à côté.
SEUIL_SURDIMENSION = 2


def capacite(salle: RessourceCatalogue) -> int:
    """Capacité déclarée d'une salle, zéro si l'attribut manque"""
    return salle.attributs.get("capacite", 0)


def filtrer_salles_par_capacite(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Ne garde que les salles dont la capacité couvre le nombre d'invités"""
    return [salle for salle in salles if capacite(salle) >= nombre_invites]


def filtrer_salles_bien_dimensionnees(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Écarte les salles démesurées : une borne haute, en plus de la borne basse.

    Proposer 800 places à qui en demande 50 n'est pas une option, c'est du
    bruit. La borne haute vaut SEUIL_SURDIMENSION fois le nombre d'invités.
    """
    return [
        salle
        for salle in salles
        if nombre_invites <= capacite(salle) <= nombre_invites * SEUIL_SURDIMENSION
    ]


def trier_salles_par_proximite(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Classe les salles de la plus juste à la plus surdimensionnée"""
    return sorted(salles, key=lambda salle: capacite(salle) - nombre_invites)


def trier_salles_par_capacite_decroissante(
    salles: list[RessourceCatalogue],
) -> list[RessourceCatalogue]:
    """Classe les salles de la plus grande à la plus petite"""
    return sorted(salles, key=capacite, reverse=True)


def trier_salles_par_quartier(
    salles: list[RessourceCatalogue], quartier_souhaite: str | None
) -> list[RessourceCatalogue]:
    """Remonte en tête les salles du quartier souhaité, sans en écarter aucune.

    Sans quartier souhaité, aucune préférence à appliquer : l'ordre reçu
    (déjà filtré par capacité) est conservé tel quel.
    """
    if quartier_souhaite is None:
        return list(salles)
    return sorted(salles, key=lambda salle: salle.attributs.get("quartier") != quartier_souhaite)


def rechercher_candidats_salle(
    salles: list[RessourceCatalogue], besoin: BesoinChiffrage
) -> list[RessourceCatalogue]:
    """Propose les salles à la taille de l'événement, ou la moins mauvaise, jamais les deux.

    Quand le catalogue contient des salles à la bonne taille, elles seules
    sont proposées, de la plus juste à la plus large, plafonnées à trois.

    Quand il n'en contient aucune, une seule salle est montrée — la plus
    petite qui puisse accueillir tout le monde, ou la plus grande du
    catalogue si aucune n'y suffit. En proposer davantage laisserait croire
    à un choix qui n'existe pas : le vrai choix est alors entre cette salle
    et un devis sur mesure.

    Le quartier trie en dernier, sur la liste déjà réduite : la taille décide
    lesquelles montrer, le quartier dans quel ordre. Aucune salle n'est
    jamais écartée pour son quartier (D17).
    """
    retenues = _retenir_salles(salles, besoin.nombre_invites)
    return trier_salles_par_quartier(retenues, besoin.quartier_souhaite)


def _retenir_salles(
    salles: list[RessourceCatalogue], nombre_invites: int
) -> list[RessourceCatalogue]:
    """Applique la règle de taille, avant tout tri par quartier"""
    bien_dimensionnees = filtrer_salles_bien_dimensionnees(salles, nombre_invites)
    if bien_dimensionnees:
        return limiter_nombre_options(
            trier_salles_par_proximite(bien_dimensionnees, nombre_invites),
            NOMBRE_MAX_OPTIONS_PAR_CATEGORIE,
        )

    suffisantes = filtrer_salles_par_capacite(salles, nombre_invites)
    if suffisantes:
        return [min(suffisantes, key=capacite)]
    if salles:
        return [max(salles, key=capacite)]
    return []


AJUSTEMENT_TROP_PETITE = "trop_petite"
AJUSTEMENT_SURDIMENSIONNEE = "surdimensionnee"
AJUSTEMENT_AJUSTE = "ajuste"


def qualifier_ajustement_salle(salle: RessourceCatalogue, nombre_invites: int) -> str:
    """Dit comment cette salle se situe par rapport au nombre d'invités.

    Sert au canal à expliquer pourquoi cette salle-là est proposée : une
    salle hors gabarit n'apparaît que faute de mieux, et le prospect doit
    l'apprendre de l'écran, pas le découvrir le jour de l'événement.
    """
    places = capacite(salle)
    if places < nombre_invites:
        return AJUSTEMENT_TROP_PETITE
    if places > nombre_invites * SEUIL_SURDIMENSION:
        return AJUSTEMENT_SURDIMENSIONNEE
    return AJUSTEMENT_AJUSTE


def devis_sur_mesure_pertinent(
    categorie: str, candidats: list[RessourceCatalogue], nombre_invites: int
) -> bool:
    """Vrai quand le catalogue ne répond pas correctement au besoin, et qu'il faut un humain.

    Trois situations : rien à proposer du tout, une salle trop petite faute
    de mieux, ou une salle démesurée par rapport au nombre d'invités. Hors
    salle, seule l'absence totale de candidat justifie un devis sur mesure :
    un menu ou une décoration n'a pas de capacité à respecter.

    C'est l'exact complément de la règle de rechercher_candidats_salle : dès
    qu'elle a dû se rabattre sur une salle hors gabarit, le sur mesure ouvre.
    """
    if not candidats:
        return True
    if categorie != CATEGORIE_SALLE:
        return False
    return all(
        qualifier_ajustement_salle(salle, nombre_invites) != AJUSTEMENT_AJUSTE
        for salle in candidats
    )


def trier_par_prix_croissant(ressources: list[RessourceCatalogue]) -> list[RessourceCatalogue]:
    """Trie les ressources du moins cher au plus cher"""
    return sorted(ressources, key=lambda ressource: ressource.prix_unitaire)


def limiter_nombre_options(
    ressources: list[RessourceCatalogue], nombre_max: int
) -> list[RessourceCatalogue]:
    """Ne garde que les nombre_max premières options"""
    return ressources[:nombre_max]


def rechercher_candidats_categorie(
    ressources_categorie: list[RessourceCatalogue],
    categorie: str,
    besoin: BesoinChiffrage,
) -> list[RessourceCatalogue]:
    """Applique la règle de sélection propre à la catégorie.

    La salle suit sa propre règle : au plus proche du nombre d'invités, avec
    repli sur les plus grandes si aucune ne suffit. Les autres catégories
    sont triées par prix croissant. Toutes sont plafonnées à
    NOMBRE_MAX_OPTIONS_PAR_CATEGORIE pour ne pas noyer le prospect (D20).
    """
    if categorie == CATEGORIE_SALLE:
        return rechercher_candidats_salle(ressources_categorie, besoin)
    ressources_triees = trier_par_prix_croissant(ressources_categorie)
    return limiter_nombre_options(ressources_triees, NOMBRE_MAX_OPTIONS_PAR_CATEGORIE)


def rechercher_candidats_par_categorie(
    ressources: list[RessourceCatalogue],
    modele: list[RegleQuantite],
    besoin: BesoinChiffrage,
) -> dict[str, list[RessourceCatalogue]]:
    """Résout les candidats de chaque catégorie attendue, dans l'ordre du modèle.

    Une catégorie sans aucun candidat reste présente avec une liste vide :
    c'est ce qui permet de l'annoncer au prospect plutôt que de la passer
    sous silence (cas d'une salle trop petite pour le nombre d'invités).
    """
    return {
        regle.categorie: rechercher_candidats_categorie(
            [ressource for ressource in ressources if ressource.categorie == regle.categorie],
            regle.categorie,
            besoin,
        )
        for regle in modele
    }


def resoudre_ressources_choisies(
    candidats_par_categorie: dict[str, list[RessourceCatalogue]],
    ids_choisis: tuple[str, ...],
) -> dict[str, RessourceCatalogue]:
    """Associe à chaque catégorie la ressource retenue pour le chiffrage.

    Une catégorie n'est retenue que si le prospect a explicitement choisi
    l'un de ses candidats, même à candidat unique : rien n'est présumé pour
    lui (voir CLAUDE.md, le devis ne contient que ce que le prospect a
    choisi). Une catégorie non choisie reste absente du résultat, le moteur
    la signalera comme non satisfaite.
    """
    retenues: dict[str, RessourceCatalogue] = {}
    for categorie, candidats in candidats_par_categorie.items():
        choisie = _trouver_candidat_choisi(candidats, ids_choisis)
        if choisie is not None:
            retenues[categorie] = choisie
    return retenues


def _trouver_candidat_choisi(
    candidats: list[RessourceCatalogue], ids_choisis: tuple[str, ...]
) -> RessourceCatalogue | None:
    """Candidat de la catégorie que le prospect a explicitement choisi"""
    return next((candidat for candidat in candidats if candidat.id in ids_choisis), None)
