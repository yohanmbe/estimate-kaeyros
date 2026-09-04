DONNEES.md 

# Données et catalogue — Estimate

Ce document est le cœur du projet. Si le modèle de données est mal posé,
tout le reste se tord.

## Principe fondateur

On n'enregistre pas « une salle de 300 places coûte 500 000 ». On
enregistre des ressources nommées et concrètes : « Salle Étoile, Bastos,
capacité 300, 500 000 FCFA la journée ». Le prix est attaché à un objet
précis, pas à une catégorie abstraite.

Conséquence : la variation de prix selon le quartier ou le prestataire
n'est pas un problème à résoudre, c'est simplement le fait que deux
ressources différentes ont deux prix différents. Une salle à Bastos et
une salle à Tsinga sont deux lignes du catalogue.

Conséquence pour le moteur : chercher une salle n'est pas un calcul,
c'est un filtre suivi d'un tri. Le filtre porte sur la capacité, seule
contrainte physique : une salle est retenue si elle peut accueillir le
nombre d'invités. Le tri porte sur le quartier souhaité, qui remonte en
tête les salles concernées sans écarter les autres. Le résultat peut
contenir zéro, une ou plusieurs ressources. On présente les options au
prospect, il choisit.

## Multi-locataires

Chaque entreprise cliente est un tenant. Toute table métier porte une
colonne tenant_id. Toute requête filtre dessus, sans exception.

Cette règle est posée dès la première table. L'ajouter après coup
reviendrait à réécrire l'application. Elle coûte une colonne et une
habitude.

## Tables

### tenant
- id, nom de l'entreprise, ville, coordonnées, date de création
- slug : identifiant court et unique utilisé dans l'URL d'accès au chat
  (par exemple « etoile »). C'est ce qui rattache un prospect à une
  entreprise sans qu'il ait à choisir.
- logo : chemin du logo, repris dans l'en-tête du PDF (voir D14)
- actif : booléen

### utilisateur
Un gestionnaire d'une entreprise cliente.
- id, tenant_id
- email : sert d'identifiant de connexion, unique
- mot_de_passe_hache : jamais de mot de passe en clair, même en
  démonstration
- nom
- actif : booléen
- date_creation, derniere_connexion

Un utilisateur appartient à un seul tenant. C'est cette appartenance qui
détermine ce qu'il voit dans le tableau de bord : la connexion établit le
tenant_id de la session, et toutes les requêtes du tableau de bord
filtrent dessus.

### ressource
La table centrale. Une ressource est tout ce qu'on peut facturer.

- id, tenant_id
- nom : « Salle Étoile », « Chaise Napoléon », « Décoration florale
  formule complète »
- categorie : salle, mobilier, restauration, decoration, sonorisation,
  personnel, logistique
- secteur : evenementiel (prévu pour accueillir hotellerie plus tard)
- unite_facturation : jour, unite, personne, forfait, heure
- prix_unitaire : entier, en FCFA (jamais de flottant sur de l'argent)
- attributs : JSON. C'est ce qui rend le modèle générique. Une salle y
  met sa capacité et son quartier. Une chaise y met son style. Une
  chambre d'hôtel y mettrait son nombre de lits.
- actif : booléen, pour retirer une ressource sans la supprimer
- date_creation, date_modification

Pourquoi un champ JSON plutôt qu'une table par catégorie : parce qu'une
table par catégorie multiplie le code et bloque l'extension. Le JSON
permet d'ajouter un type de ressource sans migration. Le prix à payer
est qu'on ne peut pas indexer finement ; à l'échelle d'un catalogue de
quelques centaines de lignes, ça n'a aucune importance.

### modele_evenement
Le patron d'un type d'événement.
- id, tenant_id, nom (« Mariage »), description
- lignes_par_defaut : JSON décrivant les catégories attendues et la règle
  de quantité associée

Exemple pour le mariage :
  salle → 1 par jour d'événement
  mobilier (chaises) → 1 par invité
  restauration → 1 par invité
  decoration → 1 forfait
  sonorisation → 1 forfait
  personnel (maître de cérémonie) → 1 forfait
  logistique (installation) → 1 forfait

Le type d'événement ne modifie jamais un prix. Il détermine quelles
prestations sont attendues et selon quelle règle on calcule les
quantités. Ce qui fait varier le prix, ce sont la ressource choisie, la
durée et les quantités.

### demande
Une conversation en cours ou terminée.
- id, tenant_id, canal (streamlit / whatsapp), identifiant_prospect
- etat : en_cours, complete, abandonnee
- besoin : JSON, le besoin structuré extrait au fil de la conversation
- date_creation, date_modification

Structure du besoin :
  type_evenement, date_evenement, ville, quartier_souhaite,
  nombre_invites, duree_jours, budget_declare,
  prestations_souhaitees, prestations_exclues, ressources_choisies

### devis
- id, tenant_id, demande_id
- lignes : JSON figé. Chaque ligne contient designation, quantite,
  prix_unitaire, montant, ressource_id
- total, devise (XAF), date_emission, date_validite
- chemin_pdf

## Indicateurs du tableau de bord

Quatre indicateurs, tous calculés par requête sur les tables demande et
devis du tenant connecté, sur une période choisie par le gestionnaire.

Nombre de demandes reçues : compte des demandes du tenant sur la période.
Montant total estimé : somme des totaux des devis émis sur la période.
Montant moyen d'une estimation : le total divisé par le nombre de devis.
Répartition des demandes par tranche d'invités : regroupement du champ
nombre_invites du besoin en trois ou quatre tranches.

Aucun indicateur de conversion n'est affiché, le produit ne sachant pas
ce qu'une demande devient après l'envoi de l'estimation (voir D08 et
D19). Les indicateurs suivent la même règle que les devis : ils sortent
d'une requête et d'un calcul Python, jamais d'une estimation.

Les lignes sont figées à l'émission. Si un prix change en octobre, le
devis émis en septembre reste consultable à l'identique. C'est simple à
faire et ça donne un argument solide : un devis est un document, pas un
calcul rejoué.

## Jeu de données de démonstration

Construit à la main, à partir de tarifs plausibles du marché camerounais.
Il ne prétend pas refléter des prix réels : il sert à démontrer le
mécanisme.

Un tenant fictif : Fanta Events

Salles à créer, huit environ, réparties sur plusieurs quartiers de
Yaoundé, avec des capacités de 50 à 800 places et des prix qui varient
selon le quartier.
[À COMPLÉTER : liste des salles avec quartier, capacité, prix journalier]

Prestations à créer, une vingtaine, couvrant les sept catégories.
[À COMPLÉTER : liste des prestations avec unité de facturation et prix]

Un utilisateur gestionnaire par tenant, créé dans le seed avec un mot de
passe haché. Identifiants de démonstration à noter dans le README, pas
dans le code.

## Pièges connus

Les montants sont des entiers en FCFA. Aucun flottant sur de l'argent :
les erreurs d'arrondi finissent par se voir sur un total.

Le prospect exprime des quantités floues (« environ 300 personnes »,
« une centaine »). L'extraction doit produire un entier ou déclarer
l'information manquante, jamais une approximation silencieuse.

Les dates arrivent sous toutes les formes (« le 12 juillet », « samedi
prochain », « mi-décembre »). Prévoir un format canonique et un cas
« date imprécise » qui déclenche une relance.

Les noms de quartiers de Yaoundé s'écrivent de plusieurs façons. Prévoir
une normalisation et une notion de proximité entre quartiers, même
grossière.