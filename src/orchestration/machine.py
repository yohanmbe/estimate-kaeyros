"""Point d'entrée de la machine à états (voir ARCHITECTURE.md, D04)

Fonction pure : aucun appel au LLM, aucun accès base ou catalogue. Elle
reçoit le besoin déjà extrait et, une fois celui-ci complet, les candidats
par catégorie déjà résolus par src/moteur/selection.py à partir du
catalogue du tenant.
"""
from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue
from src.orchestration.champs_obligatoires import identifier_champs_obligatoires_manquants
from src.orchestration.choix_ressources import identifier_prochaine_categorie_a_choisir
from src.orchestration.types import Decision, PassageChiffrage, QuestionBesoin, QuestionChoixRessources


def decider_prochaine_etape(
    besoin: Besoin,
    candidats_par_categorie: dict[str, list[RessourceCatalogue]] | None = None,
) -> Decision:
    """Détermine la prochaine étape : compléter le besoin, choisir une ressource, ou chiffrer"""
    champs_manquants = identifier_champs_obligatoires_manquants(besoin)
    if champs_manquants:
        return QuestionBesoin(champs_manquants=champs_manquants)

    prochain_choix = identifier_prochaine_categorie_a_choisir(besoin, candidats_par_categorie or {})
    if prochain_choix is not None:
        categorie, candidats = prochain_choix
        return QuestionChoixRessources(categorie=categorie, candidats=candidats)

    return PassageChiffrage()
