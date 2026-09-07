from src.catalogue.vocabulaire import (
    CATEGORIES,
    LIBELLES_CATEGORIES,
    LIBELLES_UNITES,
    UNITE_HABITUELLE,
    UNITES_FACTURATION,
    champs_attributs,
    libelle_categorie,
    libelle_unite,
)


def test_les_sept_categories_du_modele_de_donnees_sont_toutes_declarees():
    assert set(CATEGORIES) == {
        "salle",
        "mobilier",
        "restauration",
        "decoration",
        "sonorisation",
        "personnel",
        "logistique",
    }


def test_chaque_categorie_a_un_libelle_et_une_unite_habituelle():
    """Sans ça, une catégorie s'afficherait en clé brute dans l'écran catalogue"""
    for categorie in CATEGORIES:
        assert categorie in LIBELLES_CATEGORIES
        assert UNITE_HABITUELLE[categorie] in UNITES_FACTURATION


def test_chaque_unite_de_facturation_a_un_libelle():
    for unite in UNITES_FACTURATION:
        assert unite in LIBELLES_UNITES


def test_categorie_inconnue_saffiche_telle_quelle_plutot_que_de_planter():
    assert libelle_categorie("hebergement") == "hebergement"
    assert libelle_unite("semaine") == "semaine"


def test_decoration_saffiche_accentuee_alors_que_la_cle_ne_lest_pas():
    assert libelle_categorie("decoration") == "décoration"


def test_salle_demande_sa_capacite_et_son_quartier():
    """La capacité filtre les salles et le quartier les trie (D17) : le
    formulaire doit réclamer les deux, une salle sans capacité restant
    invisible au prospect.
    """
    champs = champs_attributs("salle")

    assert [champ.cle for champ in champs] == ["capacite", "quartier"]
    assert [champ.nature for champ in champs] == ["entier", "texte"]
    assert all(champ.obligatoire for champ in champs)


def test_mobilier_propose_un_style_sans_lexiger():
    champs = champs_attributs("mobilier")

    assert [champ.cle for champ in champs] == ["style"]
    assert not champs[0].obligatoire


def test_categorie_sans_attribut_ne_demande_aucun_champ_supplementaire():
    assert champs_attributs("sonorisation") == ()
    assert champs_attributs("categorie-inexistante") == ()


def test_chaque_champ_dattribut_porte_un_libelle_lisible():
    for categorie in CATEGORIES:
        for champ in champs_attributs(categorie):
            assert champ.libelle
            assert champ.libelle != champ.cle
