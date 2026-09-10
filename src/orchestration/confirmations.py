"""Ce que le prospect a tranché lui-même, et ce qu'il reste à lui faire trancher

L'extracteur signale ce qu'il a déduit au lieu de lu ; c'est ici, en Python,
qu'on décide qu'il faut le faire confirmer. Le LLM ne pose jamais la question
lui-même (voir D01, D04).

Ici vit aussi la règle inverse : une décision prise par le prospect en
cliquant ne doit jamais être effacée par une extraction ultérieure.
"""
from dataclasses import replace

from src.extraction.types import Besoin

CHAMP_DATE = "date_evenement"


def identifier_champ_en_correction(besoin: Besoin) -> str | None:
    """Le champ que le prospect vient de démentir, tant qu'il n'a pas été redonné.

    Une correction est une demande précise : elle prime sur tout le reste et
    ne porte que sur ce champ-là. Dès qu'il est rempli, elle est close.
    """
    champ = besoin.champ_en_correction
    if champ is None:
        return None
    return champ if getattr(besoin, champ, None) is None else None


def identifier_hypothese_a_confirmer(besoin: Besoin) -> tuple[str, tuple[str, ...]] | None:
    """Premier champ déduit que le prospect n'a pas encore tranché, avec les valeurs à lui proposer.

    Les dates possibles passent en premier : « ce weekend » ne désigne pas une
    valeur douteuse mais deux dates concrètes, entre lesquelles seul le
    prospect peut choisir.
    """
    if besoin.dates_possibles and CHAMP_DATE not in besoin.champs_confirmes:
        return CHAMP_DATE, besoin.dates_possibles

    for champ in besoin.champs_a_confirmer:
        if champ in besoin.champs_confirmes:
            continue
        valeur = getattr(besoin, champ, None)
        if valeur is None:
            continue
        return champ, (str(valeur),)

    return None


def reporter_choix_du_prospect(besoin_extrait: Besoin, besoin_avant: Besoin) -> Besoin:
    """Réinjecte dans le besoin fraîchement extrait ce que le prospect a décidé en cliquant.

    Ces champs n'existent pas dans le schéma JSON de l'extracteur : le LLM ne
    les lit ni ne les écrit (D04), ils ne viennent que des boutons. Sans ce
    report, le premier message envoyé après un choix l'effacerait en silence,
    puisque le besoin reconstruit par l'extracteur repart toujours à vide.

    Une hypothèse déjà confirmée est retirée de ce qui reste à confirmer :
    sinon le modèle la re-signalerait à chaque tour et le prospect
    confirmerait sans fin la même chose.
    """
    champ_en_correction = _correction_encore_ouverte(besoin_extrait, besoin_avant)
    return replace(
        besoin_extrait,
        ressources_choisies=besoin_avant.ressources_choisies,
        categories_sur_mesure=besoin_avant.categories_sur_mesure,
        champs_confirmes=besoin_avant.champs_confirmes,
        champ_en_correction=champ_en_correction,
        champs_a_confirmer=tuple(
            champ
            for champ in besoin_extrait.champs_a_confirmer
            if champ not in besoin_avant.champs_confirmes
        ),
    )


def _correction_encore_ouverte(besoin_extrait: Besoin, besoin_avant: Besoin) -> str | None:
    """Garde la correction en cours tant que le prospect n'a pas redonné la valeur.

    Le champ vient d'être redonné dans ce message même : la correction est
    close, et le besoin reprend son cours normal. La laisser ouverte
    bloquerait la conversation sur une question déjà satisfaite.
    """
    champ = besoin_avant.champ_en_correction
    if champ is None:
        return None
    return champ if getattr(besoin_extrait, champ, None) is None else None
