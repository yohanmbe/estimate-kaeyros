from src.moteur.devis import chiffrer_devis
from src.moteur.types import BesoinChiffrage, RegleQuantite, RessourceCatalogue

MODELE_MARIAGE = [
    RegleQuantite(categorie="salle", base="jour"),
    RegleQuantite(categorie="mobilier", base="invite"),
    RegleQuantite(categorie="decoration", base="forfait"),
]


def ressources_mariage_300_invites() -> dict[str, RessourceCatalogue]:
    return {
        "salle": RessourceCatalogue(
            id="salle-1",
            nom="Salle Etoile",
            categorie="salle",
            unite_facturation="jour",
            prix_unitaire=500_000,
            attributs={},
        ),
        "mobilier": RessourceCatalogue(
            id="chaise-1",
            nom="Chaise Napoleon",
            categorie="mobilier",
            unite_facturation="unite",
            prix_unitaire=2_000,
            attributs={},
        ),
        "decoration": RessourceCatalogue(
            id="deco-1",
            nom="Decoration florale complete",
            categorie="decoration",
            unite_facturation="forfait",
            prix_unitaire=300_000,
            attributs={},
        ),
    }


def test_mariage_300_invites_bastos_calcule_total_correct():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources_mariage_300_invites(), besoin)

    # 500 000 (salle) + 300 * 2 000 (chaises) + 300 000 (decoration) = 1 400 000
    assert resultat.total == 1_400_000
    assert resultat.categories_non_satisfaites == []


def test_aucun_budget_declare_ne_signale_pas_de_depassement():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources_mariage_300_invites(), besoin)

    assert resultat.depasse_budget is None


def test_total_dans_le_budget_declare_ne_signale_pas_de_depassement():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=2_000_000
    )

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources_mariage_300_invites(), besoin)

    assert resultat.depasse_budget is False


def test_total_superieur_au_budget_declare_est_signale():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=1_000_000
    )

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources_mariage_300_invites(), besoin)

    assert resultat.depasse_budget is True


def test_categorie_sans_ressource_disponible_apparait_dans_le_resultat():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )
    ressources = ressources_mariage_300_invites()
    del ressources["decoration"]

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources, besoin)

    assert [c.categorie for c in resultat.categories_non_satisfaites] == ["decoration"]
    assert resultat.total == 500_000 + 300 * 2_000


def test_mariage_aucune_salle_disponible_signale_categorie_salle_non_satisfaite():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )
    ressources = ressources_mariage_300_invites()
    del ressources["salle"]

    resultat = chiffrer_devis(MODELE_MARIAGE, ressources, besoin)

    assert [c.categorie for c in resultat.categories_non_satisfaites] == ["salle"]


def test_mariage_300_invites_calcule_300_chaises_et_300_repas_avec_montant_exact():
    modele = [
        RegleQuantite(categorie="mobilier", base="invite"),
        RegleQuantite(categorie="restauration", base="invite"),
    ]
    chaise = RessourceCatalogue(
        id="chaise-1",
        nom="Chaise Napoleon",
        categorie="mobilier",
        unite_facturation="unite",
        prix_unitaire=2_000,
        attributs={},
    )
    repas = RessourceCatalogue(
        id="repas-1",
        nom="Menu Standard",
        categorie="restauration",
        unite_facturation="personne",
        prix_unitaire=8_000,
        attributs={},
    )
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = chiffrer_devis(
        modele, {"mobilier": chaise, "restauration": repas}, besoin
    )

    lignes_par_designation = {ligne.designation: ligne for ligne in resultat.lignes}
    assert lignes_par_designation["Chaise Napoleon"].quantite == 300
    assert lignes_par_designation["Menu Standard"].quantite == 300
    # 300 chaises a 2 000 + 300 repas a 8 000 = 3 000 000 FCFA au franc pres
    assert resultat.total == 300 * 2_000 + 300 * 8_000
