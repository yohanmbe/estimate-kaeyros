"""Feuille de style du tableau de bord gestionnaire.

Parti pris : barre latérale sombre contre contenu clair. L'espace
professionnel se distingue ainsi au premier regard du chat du prospect, qui est
clair et chaleureux, sans quitter la palette Kaeyros — bleu pour les commandes
et l'état actif, orange en accent seulement, jamais pour une alerte.

Nommage BEM en français, comme dans src/canaux/streamlit_prospect.py. Les
widgets Streamlit natifs sont habillés via le motif st.container(key="x") plus
le sélecteur [class*="st-key-x"], seul moyen d'atteindre l'intérieur d'un
conteneur sans écrire de HTML à sa place.
"""

FEUILLE_DE_STYLE = """
<style>
:root{
  --bleu:#0f2a96; --bleu-fonce:#0a1f6f; --bleu-pale:#eaeefb; --bleu-pale-vif:#dde4f9;
  --orange:#ff5f00; --orange-texte:#d94f00; --orange-pale:#fff1e6;
  --encre:#101322; --encre-clair:#1b2033; --encre-trait:#2a3049;
  --gris:#5b6178; --gris-clair:#8b91a7; --trait:#e4e7f2;
  --surface:#ffffff; --fond:#f6f7fb;
  --vert-pale:#e8f6ee; --vert-texte:#1a6b3c; --vert-trait:#b6e0c7;
  --rouge-pale:#fdecee; --rouge-texte:#7a1622; --rouge-trait:#f0aab3;
}

.stApp{background:var(--fond);}
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stDecoration"], footer{display:none;}
[data-testid="stToolbar"]{background:transparent;box-shadow:none;}
[data-testid="stHeader"]{background:transparent;}
.stMainBlockContainer, .block-container{padding-top:2.2rem;padding-bottom:5rem;max-width:1180px;}
*{overflow-wrap:break-word;}

/* « Press Enter to submit form » : l'indication native de Streamlit sous un
   champ dans un formulaire. Redondante avec le bouton Enregistrer, elle
   n'apporte rien au gestionnaire et clignote à chaque frappe. */
[data-testid="InputInstructions"]{display:none !important;}

/* Bug connu des colonnes Streamlit : un flex-item garde par défaut la largeur
   de son contenu (min-width:auto), ce qui fait déborder tout texte un peu
   long hors de sa colonne au lieu d'y passer à la ligne. */
[data-testid="stColumn"]{min-width:0;}

/* Streamlit pose lui-même white-space:nowrap sur le texte des boutons : sans
   ça, une colonne un peu étroite (barre latérale dépliée sur un écran de
   portable, par exemple) fait déborder le libellé hors du bouton au lieu de
   le passer à la ligne. Un bouton sur deux lignes reste lisible ; un bouton
   qui déborde de sa carte ne l'est pas. */
.stButton>button p{white-space:normal !important;word-break:break-word;}

/* ---------- Barre latérale ---------- */
section[data-testid="stSidebar"]{background:var(--encre);border-right:1px solid var(--encre-trait);}
section[data-testid="stSidebar"][aria-expanded="true"]{min-width:280px !important;}
section[data-testid="stSidebar"] *{color:#eef0f7;}

/* La barre latérale s'étire sur toute la hauteur et devient elle-même une
   colonne flex : le bloc « pied de barre » (repéré par :has, voir plus bas)
   se pousse ainsi tout en bas, sous la navigation, même quand celle-ci est
   courte. Streamlit insère un div anonyme entre stSidebarUserContent et le
   stVerticalBlock qui empile réellement nos éléments (vérifié dans le DOM
   rendu) : les deux niveaux doivent être mis en colonne flex extensible,
   sinon la marge automatique du pied de barre n'a aucun espace où pousser. */
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{
  padding-top:1.6rem;min-height:100vh;display:flex;flex-direction:column;}
[data-testid="stSidebarUserContent"] > div{
  flex:1;display:flex;flex-direction:column;min-height:0;}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]{
  flex:1;display:flex;flex-direction:column;min-height:0;}
/* La marge automatique doit être posée sur le véritable enfant flex de
   stVerticalBlock (un stElementContainer), pas sur un descendant plus profond
   comme stMarkdownContainer : sur ce dernier, margin-top:auto n'a aucun effet
   puisqu'il n'est pas lui-même un item du conteneur flex. :has() cherche donc
   .pied-lateral à n'importe quelle profondeur sous le bon niveau. */
[data-testid="stSidebarUserContent"] [data-testid="stElementContainer"]:has(.pied-lateral){
  margin-top:auto;}

.marque{display:flex;align-items:center;gap:.6rem;margin-bottom:.15rem;}
.marque__pastille{width:1.6rem;height:1.6rem;border-radius:9px;flex:none;
  background:linear-gradient(135deg,var(--bleu) 50%,var(--orange) 50%);}
.marque__logo{height:1.8rem;width:auto;flex:none;}
.marque__nom{font-weight:800;font-size:1.15rem;letter-spacing:.01em;color:#ffffff;}
.marque__sous{font-size:.78rem;color:var(--gris-clair) !important;margin:0 0 1.4rem .1rem;}

/* Navigation : un bouton par écran. Idle, un fond et un filet très légers
   suffisent à lire « ceci est une carte cliquable, pas juste du texte » ;
   l'actif porte un fond plein et un filet orange, la flèche sert de repère
   constant de destination (une page s'ouvre), pas seulement au survol. */
[class*="st-key-lien-nav"] .stButton>button{
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  color:#c3c8da;font-weight:600;font-size:.95rem;text-align:left;justify-content:flex-start;
  padding:.6rem .85rem;border-radius:10px;box-shadow:none;width:100%;}
[class*="st-key-lien-nav"] .stButton>button p{
  display:flex;align-items:center;justify-content:space-between;width:100%;}
[class*="st-key-lien-nav"] .stButton>button p::after{
  content:"›";font-weight:800;font-size:1.05rem;color:#6b7290;margin-left:.4rem;}
[class*="st-key-lien-nav"] .stButton>button:hover{
  background:var(--encre-clair);border-color:rgba(255,255,255,.14);color:#ffffff;}
[class*="st-key-lien-nav"] .stButton>button:hover p::after{color:#c3c8da;}
[class*="st-key-lien-nav-actif"] .stButton>button{background:var(--encre-clair);color:#ffffff;
  font-weight:700;border-color:transparent;box-shadow:inset 3px 0 0 var(--orange);}
[class*="st-key-lien-nav-actif"] .stButton>button p::after{color:var(--orange);}

.pied-lateral{border-top:1px solid var(--encre-trait);margin-top:1.5rem;padding-top:1.1rem;
  display:flex;align-items:center;gap:.65rem;}
.pied-lateral__pastille{width:2.3rem;height:2.3rem;border-radius:9px;flex:none;background:var(--bleu);
  color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.8rem;}
.pied-lateral__nom{display:block;font-weight:700;font-size:.92rem;color:#ffffff;line-height:1.3;}
.pied-lateral__meta{display:block;font-size:.76rem;color:var(--gris-clair) !important;}

[class*="st-key-deconnexion"] .stButton>button{background:transparent;color:#c3c8da;
  border:1px solid var(--encre-trait);border-radius:10px;font-weight:600;padding:.5rem 0;width:100%;}
[class*="st-key-deconnexion"] .stButton>button:hover{background:var(--encre-clair);
  color:#ffffff;border-color:#3a4160;}

/* ---------- En-tête d'écran ---------- */
.titre-ecran{font-size:1.75rem;font-weight:800;color:var(--encre);letter-spacing:-.01em;
  line-height:1.2;margin:0;}
.titre-ecran__sous{font-size:.92rem;color:var(--gris);margin-top:.35rem;}

/* Filtres segmentés : Streamlit les rend en boutons radio, habillés en pilules */
[data-testid="stSegmentedControl"] button{border-radius:9px !important;font-weight:600;font-size:.86rem;}
.libelle-filtre{font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:var(--gris);
  font-weight:800;margin:.55rem 0 .2rem;}
.libelle-filtre--nb{text-align:right;}

/* Streamlit ajoute une ancre cliquable dans chaque titre de niveau 1 : sans
   intérêt sur un écran d'application, et visible au survol. */
.titre-ecran a{display:none !important;}

/* ---------- Cartes d'indicateurs ---------- */
.carte{background:var(--surface);border:1px solid var(--trait);border-radius:16px;
  padding:1.15rem 1.3rem;height:100%;min-height:9.6rem;
  box-shadow:0 1px 3px rgba(16,19,34,.04);}
.carte__libelle{font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:var(--gris);
  font-weight:800;}
.carte__valeur{font-size:2rem;font-weight:800;color:var(--encre);margin-top:.5rem;
  font-variant-numeric:tabular-nums;line-height:1.1;letter-spacing:-.02em;}
.carte__unite{font-size:.82rem;font-weight:700;color:var(--gris);margin-left:.35rem;
  letter-spacing:.02em;}
.carte__legende{font-size:.8rem;color:var(--gris-clair);margin-top:.55rem;}

/* Histogramme des tranches : effectif au-dessus, tranche en dessous */
.tranches{display:flex;align-items:flex-end;gap:.55rem;margin-top:.7rem;height:3.9rem;}
.tranche{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;
  gap:.3rem;height:100%;}
.tranche__effectif{font-size:.82rem;font-weight:800;color:var(--encre);
  font-variant-numeric:tabular-nums;}
.tranche__barre{width:100%;background:var(--bleu);border-radius:5px 5px 0 0;min-height:3px;}
.tranche__barre--vide{background:var(--trait);}
.tranche__libelle{font-size:.7rem;color:var(--gris);white-space:nowrap;}

/* ---------- Bande d'indicateurs secondaires ---------- */
.bande{background:var(--surface);border:1px solid var(--trait);border-radius:14px;
  padding:.9rem 1.2rem;display:flex;align-items:baseline;gap:.6rem;}
.bande__valeur{font-size:1.25rem;font-weight:800;color:var(--bleu);font-variant-numeric:tabular-nums;}
.bande__libelle{font-size:.84rem;color:var(--gris);}

/* ---------- Panneaux et tableaux ---------- */
.panneau-liste{background:var(--surface);border:1px solid var(--trait);border-radius:16px;
  overflow:hidden;box-shadow:0 1px 3px rgba(16,19,34,.04);}
.panneau-liste__entete{display:flex;justify-content:space-between;align-items:baseline;
  padding:1.05rem 1.3rem .85rem;border-bottom:1px solid var(--trait);}
.panneau-liste__titre{font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--gris);font-weight:800;}
.panneau-liste__compte{font-size:.8rem;color:var(--gris-clair);font-variant-numeric:tabular-nums;}
.defilement{overflow-x:auto;}

.table{width:100%;border-collapse:collapse;font-size:.88rem;}
.table th{text-align:left;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--gris);padding:.6rem 1.3rem;background:#fafbfe;font-weight:800;white-space:nowrap;
  border-bottom:1px solid var(--trait);}
.table td{padding:.8rem 1.3rem;border-top:1px solid var(--trait);color:var(--encre);
  vertical-align:middle;}
.table tbody tr:first-child td{border-top:none;}
.table tbody tr:hover{background:#fafbfe;}
/* Pas de nowrap ici : le montant lui-même reste insécable grâce aux espaces
   insécables de formater_montant, mais la devise doit pouvoir passer sous le
   montant plutôt que déborder quand la colonne est vraiment trop étroite. */
.table__nb{text-align:right;font-variant-numeric:tabular-nums;}
.table__principal{font-weight:700;color:var(--encre);}
.table__secondaire{font-size:.8rem;color:var(--gris);margin-top:.1rem;}
.table__devise{font-size:.72rem;color:var(--gris-clair);font-weight:600;margin-left:.25rem;}

/* Lignes de liste : chaque ligne est un st.container(key="ligne-...") plutôt
   qu'une ligne de <table>, pour pouvoir y poser de vrais boutons. Ces règles
   lui redonnent le filet, le rythme et le survol d'un tableau. */
[class*="st-key-ligne-"]{border-top:1px solid var(--trait);background:var(--surface);
  padding:.15rem .9rem;transition:background .12s ease;}
[class*="st-key-ligne-"]:hover{background:#fafbfe;}
[class*="st-key-ligne-"] [data-testid="stHorizontalBlock"]{align-items:center !important;}
[class*="st-key-ligne-"] .stButton>button{background:transparent;border:1px solid var(--trait);
  border-radius:9px;color:var(--bleu);font-weight:600;font-size:.82rem;padding:.3rem .7rem;
  box-shadow:none;}
[class*="st-key-ligne-"] .stButton>button:hover{background:var(--bleu-pale);
  border-color:#c7d1f6;color:var(--bleu-fonce);}
[class*="st-key-entetes-"]{padding:.2rem .9rem;background:#fafbfe;
  border:1px solid var(--trait);border-radius:10px 10px 0 0;}
[class*="st-key-entetes-"] [data-testid="stHorizontalBlock"]{align-items:center !important;}
/* La dernière ligne referme la liste, que les lignes n'ont qu'un filet haut */
[class*="st-key-ligne-"]:last-of-type{border-bottom:1px solid var(--trait);
  border-radius:0 0 10px 10px;}

/* Bloc des prestations retirées : nettement séparé de la liste active (le
   gestionnaire ne doit jamais confondre les deux), et discret plutôt que
   grisé au point de devenir illisible. */
.separateur-retirees{margin-top:2.6rem;padding-top:1.8rem;border-top:1px dashed var(--trait);}
[class*="st-key-ligne-prestation-retiree-"]{background:#fbfbfd;}
[class*="st-key-ligne-prestation-retiree-"] .table__principal{color:var(--gris);}
[class*="st-key-ligne-prestation-retiree-"]:hover{background:#f5f6fa;}
.table__secondaire--alerte{color:var(--rouge-texte);font-weight:700;}

/* Bouton Supprimer : un geste destructif se distingue des autres, même avant
   la confirmation, pour qu'on ne le confonde jamais avec Modifier ou Retirer. */
[class*="st-key-ligne-prestation-retiree-"] [class*="st-key-supprimer-"] .stButton>button{
  color:var(--rouge-texte);border-color:var(--rouge-trait);}
[class*="st-key-ligne-prestation-retiree-"] [class*="st-key-supprimer-"] .stButton>button:hover{
  background:var(--rouge-pale);border-color:#e58a95;}
[class*="st-key-confirmer-suppression-"] .stButton>button{
  background:var(--rouge-texte);border-color:var(--rouge-texte);color:#fff;box-shadow:none;}
[class*="st-key-confirmer-suppression-"] .stButton>button:hover{background:#5e1119;}

/* ---------- Pastilles ---------- */
/* white-space:normal plutôt que nowrap : une pastille de statut trop longue
   pour une colonne étroite doit passer à la ligne dans sa pilule, jamais
   déborder par-dessus la colonne suivante. */
.pastille{display:inline-flex;align-items:center;font-size:.75rem;font-weight:700;
  padding:.25rem .65rem;border-radius:999px;white-space:normal;text-align:center;
  max-width:100%;border:1px solid transparent;}
.pastille--bleu{background:var(--bleu-pale);color:var(--bleu-fonce);border-color:#c7d1f6;}
.pastille--vert{background:var(--vert-pale);color:var(--vert-texte);border-color:var(--vert-trait);}
.pastille--gris{background:#eef0f6;color:var(--gris);border-color:#dfe3ee;}
.pastille--orange{background:var(--orange-pale);color:var(--orange-texte);border-color:#ffd7b8;}
.pastille--sarcelle{background:#e4f4f4;color:#14676b;border-color:#b5e0e1;}
.pastille--violet{background:#f1ebfb;color:#5b34a8;border-color:#d7c8f3;}
.pastille--ambre{background:#fdf3d7;color:#8a6100;border-color:#f0dca2;}

/* ---------- Récapitulatif clé/valeur (même forme que le chat et le PDF) ---------- */
.recap{background:var(--surface);border:1px solid var(--trait);border-radius:14px;
  padding:1.05rem 1.25rem;}
.recap__titre{font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;
  color:var(--orange-texte);font-weight:800;margin-bottom:.5rem;}
.recap__ligne{display:flex;justify-content:space-between;gap:.75rem;font-size:.85rem;
  padding:.45rem 0;border-bottom:1px dashed var(--trait);}
.recap__ligne:last-child{border-bottom:none;padding-bottom:0;}
.recap__cle{color:var(--gris);font-weight:600;}
.recap__valeur{color:var(--bleu-fonce);font-weight:700;text-align:right;}
.recap__valeur--manquant{color:#b6bccd;font-weight:500;}

/* ---------- État vide ---------- */
.vide{background:var(--surface);border:1px dashed var(--trait);border-radius:16px;
  padding:2.4rem 1.8rem;text-align:center;}
.vide__titre{font-size:1.02rem;font-weight:700;color:var(--encre);}
.vide__texte{font-size:.88rem;color:var(--gris);margin-top:.45rem;line-height:1.6;
  max-width:34rem;margin-left:auto;margin-right:auto;}
.vide__code{display:inline-block;margin-top:.7rem;background:var(--bleu-pale);
  color:var(--bleu-fonce);border-radius:8px;padding:.3rem .6rem;font-size:.82rem;font-weight:700;}

/* ---------- Total d'un devis consulté ---------- */
.total{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;
  padding:1rem 1.3rem;background:linear-gradient(135deg,var(--bleu-pale),var(--bleu-pale-vif));}
.total__libelle{font-weight:700;color:var(--bleu-fonce);}
.total__montant{font-size:1.45rem;font-weight:800;color:var(--orange-texte);
  font-variant-numeric:tabular-nums;white-space:nowrap;}

/* ---------- Formulaires ---------- */
.stTextInput label, .stNumberInput label, .stSelectbox label{font-weight:600;color:var(--encre);
  font-size:.86rem;}
.stTextInput input, .stNumberInput input{border-radius:10px;}
[class*="st-key-carte-formulaire"]{background:var(--surface);border:1px solid var(--trait);
  border-radius:16px;padding:1.3rem 1.4rem;box-shadow:0 1px 3px rgba(16,19,34,.04);}
</style>
"""

# L'écran de connexion vit dans la même application, donc dans une page réglée
# en pleine largeur. Sans cette surcharge, un formulaire de deux champs
# s'étalerait sur tout l'écran.
STYLE_CONNEXION = """
<style>
/* Streamlit pose ses propres marges internes sur ce conteneur (env. 80px de
   chaque côté en plein écran) : sans les écraser ici, max-width ne dessine
   qu'une carte étroite dans un cadre bien plus large qu'elle. */
.stMainBlockContainer, .block-container{
  max-width:560px;padding-top:3.6rem;padding-bottom:3rem;
  padding-left:1.5rem;padding-right:1.5rem;}
.stApp{background:
    radial-gradient(1300px 900px at 6% -10%, rgba(15,42,150,.14), transparent 62%),
    radial-gradient(1100px 780px at 104% 2%, rgba(255,95,0,.12), transparent 58%),
    var(--fond);
  background-attachment:fixed;}

.marque-connexion{text-align:center;margin-bottom:1.7rem;}
.marque-connexion__nom{font-size:1.75rem;font-weight:800;color:var(--encre);letter-spacing:-.01em;}
.marque-connexion__sous{font-size:.92rem;color:var(--orange-texte);font-weight:700;margin-top:.25rem;}

[class*="st-key-carte-connexion"]{background:var(--surface);border:1px solid var(--trait);
  border-radius:20px;padding:2.3rem 2.3rem 1.6rem;box-shadow:0 12px 34px rgba(16,19,34,.10);}
[class*="st-key-carte-connexion-erreur"] .stTextInput input{
  border-color:var(--rouge-trait) !important;background:var(--rouge-pale) !important;}
[class*="st-key-carte-connexion"] .stFormSubmitButton>button{background:var(--bleu);
  color:#fff;border:none;border-radius:10px;font-weight:700;padding:.65rem 0;width:100%;}
[class*="st-key-carte-connexion"] .stFormSubmitButton>button:hover{background:var(--bleu-fonce);color:#fff;}

.alerte-connexion{background:var(--rouge-pale);border:1px solid var(--rouge-trait);
  border-radius:12px;padding:.85rem 1.05rem;margin-bottom:1rem;color:var(--rouge-texte);
  font-size:.87rem;line-height:1.5;}
.alerte-connexion__titre{font-weight:700;margin-bottom:.2rem;}
.pied-connexion{text-align:center;margin-top:1.2rem;font-size:.85rem;color:var(--gris);}
.pied-connexion a{color:var(--bleu);font-weight:600;text-decoration:none;}
</style>
"""
