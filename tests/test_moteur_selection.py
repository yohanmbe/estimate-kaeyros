from src.moteur.selection import (
    devis_sur_mesure_pertinent,
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


def test_aucune_salle_assez_grande_ne_propose_que_la_plus_grande():
    """900 invités, catalogue plafonné à 500 : une seule salle, pas un faux choix"""
    salles = [
        salle("Royale", 150, "Bastos", 300_000),
        salle("Cocotiers", 500, "Tsinga", 900_000),
        salle("Palmiers", 300, "Bastos", 600_000),
    ]
    besoin = BesoinChiffrage(
        nombre_invites=900, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Cocotiers"]


def test_salles_trop_grandes_ne_masquent_pas_celles_a_la_bonne_taille():
    """300 invités : les salles de 300 passent devant, celles de 800 disparaissent"""
    salles = [
        salle("Immense", 800, "Bastos", 900_000),
        salle("Juste", 300, "Bastos", 500_000),
        salle("Ample", 500, "Bastos", 700_000),
        salle("Pile", 320, "Bastos", 520_000),
    ]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Juste", "Pile", "Ample"]


def test_cinquante_invites_face_a_un_catalogue_de_grandes_salles():
    """Le cas exact du premier test réel : 50 invités, catalogue 400/600/800"""
    salles = [
        salle("Prestige Bastos", 400, "Bastos", 750_000),
        salle("Prestige Golf", 600, "Golf", 900_000),
        salle("Prestige Warda", 800, "Warda", 1_100_000),
    ]
    besoin = BesoinChiffrage(
        nombre_invites=50, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Prestige Bastos"]
    assert devis_sur_mesure_pertinent("salle", resultat) is True


def test_salle_demesuree_est_ecartee_meme_quand_une_autre_convient():
    """250 invités : la salle de 400 convient, celle de 800 n'a rien à faire là"""
    salles = [
        salle("Prestige Bastos", 400, "Bastos", 750_000),
        salle("Prestige Warda", 800, "Warda", 1_100_000),
    ]
    besoin = BesoinChiffrage(
        nombre_invites=250, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Prestige Bastos"]
    # Même bien dimensionnée, la salle peut être dans une autre ville : le sur
    # mesure reste une option, toujours, pour la salle (voir D46)
    assert devis_sur_mesure_pertinent("salle", resultat) is True


def test_salle_trop_petite_nest_jamais_proposee_quand_une_autre_suffit():
    salles = [salle("Petite", 100, "Bastos", 200_000), salle("Grande", 400, "Mvan", 600_000)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    resultat = rechercher_candidats_salle(salles, besoin)

    assert [s.nom for s in resultat] == ["Grande"]


def test_categorie_salle_est_plafonnee_comme_les_autres():
    besoin = BesoinChiffrage(
        nombre_invites=50, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )
    salles = [salle(f"Salle {i}", 100, "Bastos", 100_000) for i in range(5)]

    resultat = rechercher_candidats_categorie(salles, "salle", besoin)

    assert len(resultat) == 3


MODELE_DEUX_CATEGORIES = [
    RegleQuantite(categorie="salle", base="jour"),
    RegleQuantite(categorie="restauration", base="invite"),
]


def test_salle_trop_petite_est_proposee_faute_de_mieux_avec_un_devis_sur_mesure():
    ressources = [salle("Royale", 150, "Bastos", 300_000), prestation("Menu", "restauration", 8_000)]
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite="Bastos", budget_declare=None
    )

    candidats = rechercher_candidats_par_categorie(ressources, MODELE_DEUX_CATEGORIES, besoin)

    assert [r.nom for r in candidats["salle"]] == ["Royale"]
    assert devis_sur_mesure_pertinent("salle", candidats["salle"]) is True
    assert [r.nom for r in candidats["restauration"]] == ["Menu"]


def test_categorie_totalement_absente_du_catalogue_reste_presente_et_vide():
    """C'est ce qui permet de l'annoncer au prospect plutôt que de la faire disparaître"""
    besoin = BesoinChiffrage(
        nombre_invites=300, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )

    candidats = rechercher_candidats_par_categorie([], MODELE_DEUX_CATEGORIES, besoin)

    assert candidats["salle"] == []
    assert candidats["restauration"] == []


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


def besoin_pour(nombre_invites: int) -> BesoinChiffrage:
    return BesoinChiffrage(
        nombre_invites=nombre_invites, duree_jours=1, quartier_souhaite=None, budget_declare=None
    )


def test_devis_sur_mesure_propose_quand_aucune_salle_ne_suffit():
    salles = [salle("Cocotiers", 500, "Tsinga", 900_000)]

    candidats = rechercher_candidats_salle(salles, besoin_pour(900))

    assert devis_sur_mesure_pertinent("salle", candidats) is True


def test_devis_sur_mesure_propose_quand_la_salle_est_demesuree():
    """20 invités et rien en dessous de 150 places : on montre la salle, et on propose mieux"""
    salles = [salle("Royale", 150, "Bastos", 300_000)]

    candidats = rechercher_candidats_salle(salles, besoin_pour(20))

    assert [s.nom for s in candidats] == ["Royale"]
    assert devis_sur_mesure_pertinent("salle", candidats) is True


def test_devis_sur_mesure_reste_propose_meme_quand_une_salle_tombe_juste():
    """Bien dimensionnée ne veut pas dire dans la bonne ville : l'option reste ouverte"""
    salles = [salle("Juste", 300, "Bastos", 500_000), salle("Immense", 800, "Mvan", 900_000)]

    candidats = rechercher_candidats_salle(salles, besoin_pour(300))

    assert devis_sur_mesure_pertinent("salle", candidats) is True


def test_devis_sur_mesure_propose_quand_le_catalogue_na_rien_dans_la_categorie():
    assert devis_sur_mesure_pertinent("restauration", []) is True


def test_categorie_hors_salle_bien_fournie_na_pas_besoin_de_sur_mesure():
    """Un menu n'a pas de capacité à respecter : sa seule question est d'exister"""
    menus = [prestation("Menu Standard", "restauration", 8_000)]

    assert devis_sur_mesure_pertinent("restauration", menus) is False
