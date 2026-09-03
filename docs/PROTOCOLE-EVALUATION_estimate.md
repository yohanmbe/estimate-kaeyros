PROTOCOLE-EVALUATION.md

# Protocole d'évaluation — Estimate

## Pourquoi ce document

Aucun professionnel du secteur n'est disponible pour noter les devis
produits, et les prix du catalogue sont construits à la main. On ne peut
donc pas mesurer la pertinence commerciale des estimations.

Ce qu'on peut mesurer, rigoureusement, c'est que le système fait ce qu'il
prétend faire. C'est ce protocole. Il est honnête sur ce qu'il ne couvre
pas, et c'est une force dans un rapport, pas une faiblesse.

## Jeu de cas de test

Une quarantaine de demandes écrites en langage naturel, rédigées à la
main, avec pour chacune le besoin attendu et le devis attendu, établis
manuellement.

Composition visée :
  vingt cas nominaux, formulations variées, besoins complets ou partiels
  dix cas de formulation difficile : quantités floues, dates imprécises,
    orthographes de quartiers variables, phrases très courtes
  dix cas limites : budget insuffisant, capacité introuvable, quartier
    sans salle, prestations refusées, demande hors périmètre

[À COMPLÉTER : rédiger les quarante cas]

## Les quatre dimensions mesurées

### 1. Qualité de l'extraction
Pour chaque champ du besoin (type, date, ville, quartier, invités, durée,
budget, prestations) : le système a-t-il extrait la bonne valeur ?
Mesure : taux d'exactitude par champ, et taux de cas entièrement corrects.
Point d'attention : une extraction fausse est bien pire qu'une extraction
absente, puisque l'absence déclenche une relance alors que l'erreur passe.
Compter les deux séparément.

### 2. Efficacité conversationnelle
Nombre de tours nécessaires pour arriver au devis. Nombre de relances
inutiles, c'est à dire portant sur une information déjà donnée.
Mesure : moyenne et distribution.

### 3. Exactitude du chiffrage
Le devis produit correspond-il au devis attendu ? Lignes retenues,
quantités, montants, total.
Mesure : taux de devis exacts au franc près. Cette valeur doit être de
100 % sur les cas où l'extraction est correcte. Tout écart est un bug,
pas une imprécision. C'est le test le plus important du projet.

### 4. Coût et latence
Nombre d'appels au LLM par conversation, temps de réponse par tour, coût
estimé si le service était payant.

## Ce que ce protocole ne mesure pas

La pertinence commerciale des estimations, faute d'expert disponible.
Le réalisme des prix du catalogue, construits à la main.
L'acceptation par de vrais prospects.

Ces limites sont à énoncer explicitement dans le rapport, avec ce qu'il
faudrait pour les lever.

## Complément qualitatif si possible

Si une personne connaissant le secteur peut être trouvée, même en dehors
de Kaeyros, lui faire relire dix devis générés et noter la cohérence de
la composition, le réalisme des montants et la clarté du document. Dix
devis relus valent mieux que rien.
[À COMPLÉTER : personne trouvée ou non] non, pas encore