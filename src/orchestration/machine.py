"""Point d'entrée de la machine à états (voir ARCHITECTURE.md, D04)

Fonction pure : aucun appel au LLM, aucun accès base ou catalogue. Elle
reçoit le besoin déjà extrait et, une fois celui-ci complet, les candidats
par catégorie déjà résolus par src/moteur/selection.py à partir du
catalogue du tenant.
"""
from src.extraction.types import Besoin
from src.moteur.types import RessourceCatalogue
from src.orchestration.champs_obligatoires import identifier_champs_obligatoires_manquants
from src.orchestration.choix_ressources import (
    devis_sur_mesure_possible,
    identifier_prochaine_categorie_a_choisir,
)
from src.orchestration.confirmations import (
    identifier_champ_en_correction,
    identifier_hypothese_a_confirmer,
)
from src.orchestration.types import (
    Decision,
    PassageChiffrage,
    QuestionBesoin,
    QuestionChoixRessources,
    QuestionComplements,
    QuestionConfirmation,
)


def decider_prochaine_etape(
    besoin: Besoin,
    candidats_par_categorie: dict[str, list[RessourceCatalogue]] | None = None,
    complements_fournis: bool = False,
) -> Decision:
    """Détermine la prochaine étape de la conversation.

    Dans l'ordre : reprendre une correction demandée, trancher une hypothèse,
    compléter le besoin, choisir les ressources, recueillir les compléments
    libres, puis chiffrer.

    Une correction passe avant tout : quand le prospect vient de dire « ce
    n'est pas la date », lui répondre autre chose — une confirmation sur le
    type d'événement, ou la liste de tout ce qui manque — donne le sentiment
    de ne pas avoir été écouté.

    La confirmation vient ensuite, avant les champs manquants. Sans cela,
    « ce weekend » resterait bloqué : la date n'est pas encore choisie, donc
    elle compte comme manquante, et on redemanderait au prospect une
    information qu'il vient précisément de donner.

    complements_fournis vient du canal, pas du besoin : ce que le prospect
    écrit en clair pour l'entreprise est stocké sur la demande, jamais mêlé
    au besoin structuré que produit l'extraction.
    """
    champ_en_correction = identifier_champ_en_correction(besoin)
    if champ_en_correction is not None:
        return QuestionBesoin(champs_manquants=(champ_en_correction,))

    hypothese = identifier_hypothese_a_confirmer(besoin)
    if hypothese is not None:
        champ, valeurs_proposees = hypothese
        return QuestionConfirmation(champ=champ, valeurs_proposees=valeurs_proposees)

    champs_manquants = identifier_champs_obligatoires_manquants(besoin)
    if champs_manquants:
        return QuestionBesoin(champs_manquants=champs_manquants)

    prochain_choix = identifier_prochaine_categorie_a_choisir(besoin, candidats_par_categorie or {})
    if prochain_choix is not None:
        categorie, candidats = prochain_choix
        return QuestionChoixRessources(
            categorie=categorie,
            candidats=candidats,
            devis_sur_mesure_possible=devis_sur_mesure_possible(besoin, categorie, candidats),
        )

    if not complements_fournis:
        return QuestionComplements()

    return PassageChiffrage()
