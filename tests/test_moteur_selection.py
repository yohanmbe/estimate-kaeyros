from src.moteur.selection import (
    filtrer_salles_par_capacite,
    rechercher_candidats_categorie,
    rechercher_candidats_par_categorie,
    rechercher_candidats_salle,
    resoudre_ressources_choisies,
    trier_salles_par_quartier,
)
from src.moteur.types import BesoinChiffrage, RegleQuantite, RessourceCatalogue


def salle(nom: str, capacite: int, quartier: str, prix: int) -> RessourceCatalogue:
    return RessourceCatalogue(
        id=nom,
        nom=nom,
        categorie="salle",
        unite_facturation="jour",
        prix_unitaire=prix,
        attributs={"capacite": capacite, "quartier": quartier},
    )


def prestation(nom: str, categorie: str, prix: int) -> RessourceCatalogue:
    return RessourceCatalogue(
        id=nom,
        nom=nom,
        categorie=categorie,
        unite_facturation="forfait",
        prix_unitaire=prix,
        attributs={},
    )


def test_salle_capacite_insuffisante_est_ecartee():
    salles = [salle("Royale", 150, "Bastos", 300_000), salle("Etoile", 300, "Bastos", 500_000)]

    resultat = filtrer_salles_par_capacite(salles, nombre_invites=300)

    assert [s.nom for s in resultat] == ["Etoile"]


def test_salle_capacite_egale_au_nombre_invites_est_retenue():
    salles = [salle("Etoile", 300, "Bastos", 500_000)]

    resultat = filtrer_salles_par_capacite(salles, nombre_invites=300)

    assert [s.nom for s in resultat] == ["Etoile"]


def test_salle_quartier_souhaite_remonte_en_tete_sans_ecarter_les_autres():
    salles = [salle("Zenith", 400, "Tsinga", 450_000), salle("Etoile", 300, "Bastos", 500_000)]

    resultat = trier_salles_par_quartier(salles, quartier_souhaite="Bastos")

    assert [s.nom for s in resultat] == ["Etoile", "Zenith"]


def test_salle_hors_quartier_reste_proposee_si_aucune_dans_le_quartier_souhaite():
    salles = [salle("Zenith", 400, "Tsinga", 450_000)]

    resultat = trier_salles_par_quartier(salles, quartier_souhaite="Bastos")

    assert [s.nom for s in resultat] == ["Zenith"]


def test_absence_de_quartier_souhaite_ne_change_pas_l_ordre():
    salles = [salle("Zenith", 400, "Tsinga", 450_000), salle("Etoile", 300, "Bastos", 500_000)]

    resultat = trier_salles_par_quartier(salles, quartier_souhaite=None)

    assert [s.nom for s in resultat] == ["Zenith", "Etoile"]


def test_mariage_300_invites_bastos_filtre_puis_trie_les_salles():
    salles = [
        salle("Royale", 150, "Bastos", 300_000),
        salle("Zenith", 400, "Tsinga", 450_000),
        salle("Etoile", 300, "Bastos", 500_000),
    ]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Etoile", "Zenith"]


def test_categorie_hors_salle_limitee_a_trois_options_triees_par_prix():
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )
    restaurations = [
        prestation("Menu Prestige", "restauration", 15_000),
        prestation("Menu Standard", "restauration", 8_000),
        prestation("Menu Confort", "restauration", 10_000),
        prestation("Menu Luxe", "restauration", 20_000),
    ]

    resultat = rechercher_candidats_categorie(restaurations, "restauration", besoin)

    assert [r.nom for r in resultat] == ["Menu Standard", "Menu Confort", "Menu Prestige"]


def test_mariage_une_seule_salle_capacite_suffisante_est_proposee():
    salles = [salle("Etoile", 300, "Bastos", 500_000)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Etoile"]


def test_mariage_aucune_salle_navait_la_capacite_suffisante_ne_renvoie_rien():
    salles = [salle("Royale", 150, "Bastos", 300_000), salle("Cocotiers", 100, "Tsinga", 200_000)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert resultat == []


def test_categorie_salle_ne_subit_aucune_limite_de_nombre():
    besoin = BesoinChiffrage(
        nombre_invites=50, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )
    salles = [salle(f"Salle {i}", 100, "Bastos", 100_000) for i in range(5)]

    resultat = rechercher_candidats_categorie(salles, "salle", besoin)

    assert len(resultat) == 5


MODELE_DEUX_CATEGORIES = [
    RegleQuantite(categorie="salle", base="jour"),
    RegleQuantite(categorie="restauration", base="invite"),
]


def test_categorie_sans_aucune_salle_assez_grande_reste_presente_et_vide():
    ressources = [salle("Royale", 150, "Bastos", 300_000), prestation("Menu", "restauration", 8_000)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    candidats = rechercher_candidats_par_categorie(ressources, MODELE_DEUX_CATEGORIES, besoin)

    assert candidats["salle"] == []
    assert [r.nom for r in candidats["restauration"]] == ["Menu"]


def test_categorie_absente_du_modele_nest_pas_proposee():
    ressources = [prestation("Chaise", "mobilier", 1_500)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    candidats = rechercher_candidats_par_categorie(ressources, MODELE_DEUX_CATEGORIES, besoin)

    assert list(candidats) == ["salle", "restauration"]


def test_categorie_a_candidat_unique_nest_pas_retenue_sans_choix_du_prospect():
    candidats = {"restauration": [prestation("Menu", "restauration", 8_000)]}

    retenues = resoudre_ressources_choisies(candidats, ids_choisis=())

    assert retenues == {}


def test_categorie_a_candidat_unique_est_retenue_une_fois_choisie():
    candidats = {"restauration": [prestation("Menu", "restauration", 8_000)]}

    retenues = resoudre_ressources_choisies(candidats, ids_choisis=("Menu",))

    assert retenues["restauration"].nom == "Menu"


def test_ressource_choisie_par_le_prospect_prime_sur_les_autres_candidates():
    candidats = {
        "restauration": [
            prestation("Menu Standard", "restauration", 8_000),
            prestation("Menu Prestige", "restauration", 15_000),
        ]
    }

    retenues = resoudre_ressources_choisies(candidats, ids_choisis=("Menu Prestige",))

    assert retenues["restauration"].nom == "Menu Prestige"


def test_categorie_sans_candidat_nest_associee_a_aucune_ressource():
    retenues = resoudre_ressources_choisies({"salle": []}, ids_choisis=())

    assert retenues == {}
