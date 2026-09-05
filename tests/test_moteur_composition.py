from src.moteur.composition import composer_devis, composer_ligne
from src.moteur.types import BesoinChiffrage, RegleQuantite, RessourceCatalogue

BESOIN = BesoinChiffrage(
    nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
)


def test_composer_ligne_calcule_le_montant_comme_prix_fois_quantite():
    chaise = RessourceCatalogue(
        id="chaise-1",
        nom="Chaise Napoleon",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=2_000,
        attributs={},
    )

    ligne = composer_ligne(chaise, quantite=300)

    assert ligne.montant == 600_000
    assert ligne.ressource_id == "chaise-1"


def test_ressource_choisie_produit_une_ligne_avec_montant_correct():
    modele = [RegleQuantite(categorie="salle", base="jour")]
    etoile = RessourceCatalogue(
        id="salle-1",
        nom="Salle Etoile",
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=500_000,
        attributs={},
    )

    lignes, categories_non_satisfaites = composer_devis(modele, {"salle": etoile}, BESOIN)

    assert categories_non_satisfaites == []
    assert lignes[0].montant == 500_000


def test_ressource_absente_produit_une_categorie_non_satisfaite():
    modele = [RegleQuantite(categorie="sonorisation", base="forfait")]

    lignes, categories_non_satisfaites = composer_devis(modele, {}, BESOIN)

    assert lignes == []
    assert [c.categorie for c in categories_non_satisfaites] == ["sonorisation"]
