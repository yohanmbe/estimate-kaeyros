# Estimate

Agent conversationnel de pré-cotation pour le secteur événementiel.

Un prospect décrit son mariage en langage courant. En quelques échanges, il
reçoit une estimation chiffrée en PDF, à l'en-tête de l'entreprise qui lui a
donné le lien. Côté entreprise, la demande arrive qualifiée dans un tableau de
bord, avec les coordonnées de rappel du prospect.

Le produit est multi-locataires : chaque entreprise cliente a son propre
catalogue, son propre lien de chat et son propre espace de gestion.

---

## Le problème

Chiffrer une demande coûte du temps à un commercial : comprendre le besoin,
retrouver les prix, composer le devis. Beaucoup de demandes ne sont jamais
chiffrées, ou le sont trop tard. Estimate automatise cette première étape, et
s'arrête là : la disponibilité, la réservation et la facturation restent chez
l'entreprise cliente et dans ses outils.

## La règle non négociable

**Le LLM extrait le besoin et reformule. Il ne calcule jamais un montant, ne
choisit jamais une ressource, ne pilote jamais la conversation.**

Tout chiffre du PDF sort d'une requête sur le catalogue suivie d'un calcul
Python déterministe et testé. Aucun montant ne provient du modèle de langage.

C'est la contrainte structurante du projet, pas une précaution : elle rend
chaque devis auditable ligne par ligne, reproductible à l'identique et
vérifiable au franc près par des tests automatisés. Une conversation un peu
moins libre qu'un agent autonome est le prix assumé de cette garantie.

## Architecture

Quatre couches qui ne se mélangent pas. Le découpage est ce qui rend le système
testable : on ne peut vérifier ni un total ni une question posée si le LLM
pilote l'ensemble.

```
  Prospect
     │  « mariage à Yaoundé en juillet, environ 300 personnes »
     ▼
┌─────────────────┐   Reçoit et renvoie des messages. Ne sait rien du métier.
│     CANAL       │   Sa seule responsabilité métier : résoudre le tenant
│  src/canaux/    │   (slug dans l'URL), au premier message et une fois pour toutes.
└────────┬────────┘
         ▼
┌─────────────────┐   Transforme une phrase en besoin structuré.
│   EXTRACTION    │   Seul endroit où le LLM travaille. Un appel par tour.
│ src/extraction/ │   Interface maison : le fournisseur est interchangeable.
└────────┬────────┘
         ▼
┌─────────────────┐   Compare le besoin aux informations obligatoires,
│  ORCHESTRATION  │   produit la question suivante ou passe au chiffrage.
│src/orchestration│   Machine à états en Python. Aucun LLM ici.
└────────┬────────┘
         ▼
┌─────────────────┐   Sélectionne les ressources, applique les règles de
│     MOTEUR      │   quantité, compose les lignes, additionne.
│   src/moteur/   │   Déterministe : même entrée, même sortie, toujours.
└────────┬────────┘
         ▼
    PDF de devis  ──▶  Demande + devis figés en base  ──▶  Tableau de bord
```

Deux principes de données portent le reste :

- **Ressources nommées, pas catégories abstraites.** Le catalogue enregistre
  « Salle Étoile, Bastos, 300 places, 450 000 FCFA/jour », jamais « salle 300
  places : 450 000 ». La variation de prix selon le lieu ou le prestataire n'est
  alors plus un problème à résoudre : ce sont deux lignes différentes.
- **Cloisonnement dès la première table.** Toute table métier porte `tenant_id`,
  toute requête filtre dessus. Une requête sans filtre est un bug de sécurité,
  pas un oubli — et c'est vérifié par les tests, pas seulement affirmé.

Le détail des arbitrages, avec leurs contreparties, est dans
[docs/DECISIONS_estimate.md](docs/DECISIONS_estimate.md).

## Périmètre de la v1

| Couvert | Hors périmètre |
|---|---|
| Type d'événement : mariage | Autres types d'événements, autres secteurs |
| Canal web (Streamlit) | Canal WhatsApp (architecture prête, non implémenté) |
| Estimation chiffrée et PDF | Disponibilité, réservation, paiement, facturation |
| Catalogue par entreprise, éditable | Comparaison de plusieurs fournisseurs |
| Tableau de bord et indicateurs | Suivi commercial, taux de conversion |
| Authentification gestionnaire | Récupération de mot de passe, rôles multiples |

Le modèle de données prévoit ces extensions sans les implémenter : rien dans les
tables n'est propre à l'événementiel.

## Démarrage rapide

### Prérequis

- Python 3.13
- PostgreSQL, avec une base `estimate_db`
- [uv](https://docs.astral.sh/uv/) pour les dépendances et l'exécution
- Une clé d'API Groq (palier gratuit suffisant) — facultative : le fournisseur
  `mock` fait tourner l'application sans aucun appel réseau

### 1. Installation

```bash
git clone <url-du-depot>
cd estimate
uv sync
```

### 2. Configuration

```bash
cp .env.example .env
```

Puis renseigner :

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/estimate_db
LLM_PROVIDER=groq          # groq, mistral ou mock
GROQ_API_KEY=...
```

`.env` n'est jamais commité. Seul `.env.example` est versionné.

### 3. Schéma de la base

```bash
uv run alembic upgrade head
```

Les migrations sont la seule façon de faire évoluer le schéma : jamais de
modification manuelle.

### 4. Jeu de démonstration

```bash
uv run python data/seed/seed.py                      # 4 entreprises, catalogues, gestionnaires
uv run python data/seed/demonstration.py etoile      # demandes et devis d'exemple
```

Les deux scripts sont idempotents. Les entreprises créées, leurs slugs et les
identifiants de connexion du tableau de bord sont listés dans
[data/seed/README.md](data/seed/README.md). Les mots de passe sont hachés en
base, y compris en démonstration.

Le script de démonstration passe par le vrai chemin de production —
enregistrement du prospect, ouverture de la demande, chiffrage sur le catalogue
réel, émission du devis. Un total de démonstration est donc un total que le
moteur produirait.

### 5. Lancer

Le chat du prospect, avec le slug de l'entreprise dans l'URL :

```bash
uv run streamlit run src/canaux/streamlit_prospect.py
# puis ouvrir http://localhost:8501/?slug=etoile
```

Sans slug valide, la conversation ne démarre pas : sans entreprise, il n'y a pas
de catalogue, donc aucun montant possible.

Le tableau de bord du gestionnaire, sur un autre port :

```bash
uv run streamlit run dashboard/app.py --server.port 8502
```

Le tenant y est établi par la connexion, jamais par un paramètre d'URL ni par
une liste déroulante.

## Déploiement de test

L'ensemble tient sur trois services gratuits : une base PostgreSQL infogérée
([Neon](https://neon.tech), palier gratuit sans expiration), deux applications
Streamlit sur [Streamlit Community Cloud](https://share.streamlit.io) — le chat
et le tableau de bord sont deux déploiements du même dépôt — et le palier
gratuit de Groq déjà utilisé en développement.

`requirements.txt` sert à cet hébergement ; `pyproject.toml` et uv restent la
référence en développement.

### 1. La base

Créer un projet Neon, récupérer sa chaîne de connexion, puis créer le schéma et
les données depuis le poste local en pointant `DATABASE_URL` vers Neon :

```bash
uv run alembic upgrade head
uv run python data/seed/seed.py
uv run python data/seed/demonstration.py etoile
```

Garder ensuite cette même base en développement évite d'entretenir deux jeux de
données divergents.

### 2. Les deux applications

Sur Streamlit Community Cloud, déployer deux fois le même dépôt :

| Application | Fichier principal | Secrets à renseigner |
|---|---|---|
| Chat du prospect | `src/canaux/streamlit_prospect.py` | `DATABASE_URL`, `LLM_PROVIDER`, `GROQ_API_KEY` |
| Tableau de bord | `dashboard/app.py` | `DATABASE_URL` |

Les secrets se saisissent dans l'interface de Streamlit Cloud, au format TOML.
Ils sont exposés au processus comme variables d'environnement, ce que
`src/db/session.py` et `src/extraction/fabrique.py` lisent déjà : aucun code à
adapter. Si Python 3.13 n'est pas proposé, 3.12 convient — le code n'utilise
aucune syntaxe postérieure.

L'adresse du chat porte le slug de l'entreprise :
`https://<votre-app>.streamlit.app/?slug=etoile`

### 3. Avant d'ouvrir l'accès à qui que ce soit

- **Changer les mots de passe de démonstration.** Ceux de
  [data/seed/README.md](data/seed/README.md) sont publics par construction.
  `provisionner_tenant` ne touche jamais au mot de passe d'un compte déjà
  créé (pour ne pas écraser en silence un mot de passe changé côté client),
  donc relancer `seed.py` ou `ajouter_tenant.py` ne suffit pas : utiliser
  `data/seed/changer_mot_de_passe.py`, un par gestionnaire.
  ```bash
  uv run python data/seed/changer_mot_de_passe.py gestionnaire@etoile.com
  ```
- **Ne déposer aucune donnée de client réel** sur un déploiement de test.
- Vérifier que `.env` n'est pas suivi par git avant de rendre le dépôt public.

### Limites de l'hébergement gratuit

La base Neon se met en veille après quelques minutes sans activité et se
réveille à la première requête : compter quelques secondes. Une application
Streamlit inactive plusieurs jours s'endort de la même façon. Avant une
démonstration, ouvrir les deux adresses une fois pour les réveiller.

## Structure du dépôt

Les modules portent le nom de leur fonction, jamais celui du produit.

```
src/
  canaux/          Interfaces prospect, résolution du tenant, écriture demande/devis
  extraction/      Interface LLM, implémentations Groq et Mistral, mock
  orchestration/   Machine à états, champs obligatoires, questions
  moteur/          Sélection des ressources, règles de quantité, calcul du devis
  catalogue/       Accès aux ressources, vocabulaire, édition, provisionnement
  consultation/    Lecture des demandes et de leurs devis
  indicateurs/     KPI du tableau de bord et périodes d'analyse
  presentation/    Mise en forme partagée des montants
  auth/            Connexion gestionnaire, hachage des mots de passe
  pdf/             Génération du document
  db/              Modèles SQLAlchemy, migrations Alembic
dashboard/         Tableau de bord Streamlit (entrée : dashboard/app.py)
data/
  seed/            Jeu de démonstration et provisionnement
  clients/         Configurations des vraies entreprises (hors dépôt)
  logos/           Logos repris dans l'en-tête des PDF
docs/              Conception, décisions, modèle de données, protocole d'évaluation
tests/
```

## Tests

```bash
uv run pytest -m "not integration"    # suite déterministe, aucun appel réseau
uv run pytest -m integration          # appelle un vrai LLM, nécessite une clé d'API
```

Aucun test de la suite déterministe n'appelle un vrai modèle de langage ni une
vraie base : le mock est forcé par une fixture globale, et le schéma est recréé
sur une base SQLite jetable à chaque test.

Le moteur de devis est testé en premier et le plus finement : c'est lui qui
produit les montants. Le cloisonnement multi-locataires l'est explicitement, par
quatre filets superposés — dont un écouteur SQLAlchemy qui fait échouer le test
dès qu'une requête touche une table métier sans filtrer sur `tenant_id`.

Un test porte le nom du cas qu'il couvre, pas celui de la fonction testée :

```
test_mariage_300_invites_bastos_calcule_total_correct
```

## Ajouter une entreprise cliente

Chaque entreprise a son catalogue et ses prix, qui n'ont rien à faire dans le
code source. Une configuration se décrit dans un fichier JSON gardé hors du
dépôt :

```bash
uv run python data/seed/ajouter_tenant.py data/clients/mon-client.json
```

Marche à suivre complète, champs attendus et gestion du logo :
[data/clients/README.md](data/clients/README.md).

## Documentation

| Document | Contenu |
|---|---|
| [CAHIER-DES-CHARGES](docs/CAHIER-DES-CHARGES_estimate.md) | Besoin, frontière du produit, critères d'acceptation |
| [ARCHITECTURE](docs/ARCHITECTURE_estimate.md) | Les quatre couches, le flux, les alternatives écartées |
| [DONNEES](docs/DONNEES_estimates.md) | Modèle de données, tables, pièges connus |
| [DECISIONS](docs/DECISIONS_estimate.md) | Journal des arbitrages, un par entrée, avec sa raison |
| [CONVENTIONS](docs/CONVENTIONS_estimate.md) | Règles de code et de nommage |
| [PROTOCOLE-EVALUATION](docs/PROTOCOLE-EVALUATION_estimate.md) | Ce qui est mesuré, et ce qui ne peut pas l'être |

## État du projet

Le parcours complet fonctionne de bout en bout : conversation, extraction,
chiffrage, PDF, écriture en base, tableau de bord. La suite déterministe compte
plus de 320 tests.

Limites assumées à ce stade :

- Le canal WhatsApp n'est pas implémenté. L'architecture le prévoit — le
  parcours métier est déjà hors du canal — mais rien n'est branché.
- La campagne d'évaluation décrite dans le protocole n'a pas encore été menée.
- Les prix du catalogue de démonstration sont construits à la main à partir de
  tarifs plausibles du marché camerounais. Ils démontrent le mécanisme, ils ne
  reflètent pas des tarifs réels.
- L'authentification est volontairement minimale (voir D18) : le cloisonnement
  entre entreprises est réel et testé, mais le durcissement des comptes reste à
  faire.

Le devis produit est une estimation indicative et non contractuelle : le PDF
porte cette mention, et aucune date de validité n'y est apposée, le produit
n'étant pas en mesure de tenir un engagement commercial (voir D31).
