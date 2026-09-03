CONVENTIONS.md

# Conventions — Estimate

## Code
Python 3.11 ou plus. Formatage par un outil automatique, jamais à la main.
Annotations de types sur les fonctions publiques.
Noms de fonctions et variables en anglais, commentaires et docstrings en
français. Le code se lit en anglais, le raisonnement s'explique en
français.
Une fonction fait une chose. Si son nom contient « et », la couper.
Les modules portent le nom de leur fonction (moteur, catalogue,
extraction), jamais le nom du produit. « estimate » est un mot anglais
courant : ne jamais l'employer comme nom de variable ou de fonction.

## Argent
Toujours des entiers, en FCFA. Aucun flottant. La devise est explicite
partout (FCFA), jamais implicite.

## Base de données
Nom de la base : estimate_db
Toute table métier porte tenant_id. Toute requête filtre dessus. Cette
règle n'a pas d'exception.
Migrations versionnées. Jamais de modification manuelle du schéma.
La donnée de démonstration vit dans data/seed/, chargée par un script,
jamais insérée à la main.

## Tests
Le moteur de devis est testé en premier, avant d'être écrit si possible.
C'est le composant qui garantit l'absence de montant inventé, donc c'est
celui dont les tests comptent le plus.
Aucun test n'appelle un vrai LLM ni une vraie base : mock et base de test.
Un test porte un nom qui décrit le cas, pas la fonction testée.

## Secrets
Clés d'API et identifiants dans des variables d'environnement. Un fichier
d'exemple versionné, le vrai fichier jamais commité.

## Commits
Message court à l'impératif, en français, préfixé par la zone touchée.
Exemple : moteur: calcule les quantités selon le modèle d'événement
Un commit par intention. Pas de commit fourre-tout en fin de journée.

## Ce qu'on ne fait pas
Pas de logique métier dans un notebook. Les notebooks servent à explorer.
Pas de nouvelle dépendance sans raison écrite dans DECISIONS.md.
Pas de code mort laissé « au cas où ».