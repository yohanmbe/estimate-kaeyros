# CLAUDE.md — Instructions pour Claude Code

Tu travailles sur Estimate, un agent conversationnel de pré-cotation pour
le secteur événementiel. Le prospect décrit son événement en langage
naturel et reçoit une estimation chiffrée en PDF. Le produit est vendu à
des entreprises événementielles (multi-locataires).

## Règle non négociable

Le LLM extrait le besoin et reformule. Il ne calcule jamais un montant,
ne choisit jamais une ressource, ne pilote jamais la conversation. Tout
montant sort d'une requête en base puis d'un calcul Python déterministe.
Si une solution viole cette règle, signale-le avant de la proposer.

## Périmètre v1

Mariage uniquement. Canal Streamlit d'abord. Sont exclus : disponibilité,
réservation, paiement, comparaison de fournisseurs, multi-secteurs. Le
modèle de données prévoit ces extensions sans les implémenter.

## Stack

Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Streamlit, fpdf2,
pytest, python-dotenv. Pas de nouvelle dépendance sans demander.

## Conventions de code

Python, annotations de types sur les fonctions publiques. Noms de
fonctions et variables en anglais, commentaires et docstrings en français.
Une fonction fait une chose. Si son nom contient « et », la couper.
Le mot « estimate » ne doit jamais être utilisé comme nom de variable ou
de fonction (c'est un mot anglais courant, ça crée des collisions).

## Conventions d'argent

Toujours des entiers, en FCFA. Aucun flottant. La devise est explicite
partout.

## Base de données

Nom : estimate_db. Toute table métier porte tenant_id. Toute requête
filtre dessus, sans exception. Migrations via Alembic, jamais de
modification manuelle du schéma.

## Structure des modules

Les modules portent le nom de leur fonction, pas le nom du produit :
- src/canaux/ — interfaces Streamlit et WhatsApp
- src/extraction/ — interface LLM, prompts, mock
- src/orchestration/ — machine à états, questions
- src/moteur/ — calcul du devis, règles de quantité
- src/catalogue/ — accès aux ressources
- src/pdf/ — génération du document
- src/db/ — modèles SQLAlchemy, migrations
- dashboard/ — interface gestionnaire Streamlit
- tests/
- data/seed/ — jeu de démonstration

## Tests

Le moteur de devis est testé en premier. Aucun test n'appelle un vrai
LLM ni une vraie base : mock et base de test. Un test porte un nom qui
décrit le cas, pas la fonction testée.
Exemple : test_mariage_300_invites_bastos_calcule_total_correct

## Secrets

Clés d'API dans des variables d'environnement (.env). Le fichier .env
n'est jamais commité. Le fichier .env.example est versionné.

## Commits

Message court à l'impératif, en français, préfixé par la zone touchée.
Exemple : moteur: calcule les quantités selon le modèle d'événement
Un commit par intention.

## Contexte complet

Les documents de conception sont dans docs/. Lis-les pour comprendre
l'architecture, les décisions et le modèle de données avant de coder.
Les fichiers importants : ARCHITECTURE.md, CONVENTIONS.md, DECISIONS.md,
DONNEES.md, CAHIER-DES-CHARGES.md.

## Comportement attendu

L'étudiant doit pouvoir expliquer chaque ligne de code à l'oral. Avant
de proposer une solution complexe, explique le raisonnement. Signale les
hypothèses. Signale si une solution viole la contrainte architecturale.
