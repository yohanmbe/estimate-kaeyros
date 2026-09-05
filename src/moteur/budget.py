"""Vérification du dépassement d'un budget déclaré"""


def verifier_depassement_budget(total: int, budget_declare: int | None) -> bool | None:
    """None si aucun budget n'a été déclaré, sinon True si le total dépasse le budget"""
    if budget_declare is None:
        return None
    return total > budget_declare
