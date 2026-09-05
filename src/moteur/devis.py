"""Point d'entrée public du moteur de devis"""
from src.moteur.budget import verifier_depassement_budget
from src.moteur.composition import composer_devis
from src.moteur.types import BesoinChiffrage, RegleQuantite, ResultatChiffrage, RessourceCatalogue


def chiffrer_devis(
    modele: list[RegleQuantite],
    ressources_choisies: dict[str, RessourceCatalogue],
    besoin: BesoinChiffrage,
) -> ResultatChiffrage:
    """Assemble les lignes, le total, les catégories non satisfaites et l'alerte budget"""
    lignes, categories_non_satisfaites = composer_devis(modele, ressources_choisies, besoin)
    total = sum(ligne.montant for ligne in lignes)
    return ResultatChiffrage(
        lignes=lignes,
        total=total,
        categories_non_satisfaites=categories_non_satisfaites,
        depasse_budget=verifier_depassement_budget(total, besoin.budget_declare),
    )
