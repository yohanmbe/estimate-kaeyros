PLAN-RAPPORT_estimate.md 

# Plan du rapport — Estimate

Format départemental ENSPY (format Tchoumi), cinq chapitres, modélisation
UML requise. Rapport écrit, pas de soutenance orale annoncée à ce jour,
mais rédiger comme si je devais le défendre.

[À COMPLÉTER : confirmer le format exact et la date de rendu auprès de
l'encadrant académique. Confirmer aussi que le changement de sujet, par
rapport au projet initial EASE Travel, est accepté.] j'ai changé, oui

## Chapitre 1 — Contexte et problématique
Kaeyros Analytics, son activité, son écosystème technique. Le secteur
événementiel et la charge que représente le chiffrage manuel d'une
demande. La commande reçue. La problématique : comment produire une
estimation fiable à partir d'une demande exprimée en langage courant,
sans qu'aucun montant ne soit inventé.
Introduire le nom une seule fois : la solution est nommée Estimate, du
nom de sa fonction, produire une estimation à partir d'une demande
exprimée en langage naturel. Ensuite employer « Estimate » ou « l'agent ».

## Chapitre 2 — État de l'art
Agents conversationnels et extraction d'information par modèle de langage.
Configurateurs de produits et moteurs de tarification. La question du
risque d'hallucination sur des données chiffrées. Positionnement : ce qui
distingue ce travail est la séparation stricte entre le langage et le
calcul.
[À COMPLÉTER : références bibliographiques]

## Chapitre 3 — Analyse et conception
Recueil des besoins et périmètre. Diagrammes UML : cas d'utilisation,
classes, séquence d'une conversation complète, états de l'orchestrateur,
déploiement. Modèle de données et justification du choix des ressources
nommées. Architecture en quatre couches et raisons du découpage.
Alternatives écartées, avec leurs contreparties : agent autonome,
automatisation graphique, RAG sur les prix.
### La frontière du produit
Estimate s'arrête à l'estimation. La vérification des disponibilités, la
réservation, la facturation et le suivi commercial restent du ressort de
l'entreprise cliente, qui dispose déjà de ses propres processus pour
cela. Cette frontière est un choix de conception, pas une limite
subie : elle garde le produit installable chez n'importe quelle
entreprise sans toucher à son organisation existante. Un outil qui
prétendrait gérer la réservation entrerait en conflit avec les outils
déjà en place chez le client.

## Chapitre 4 — Réalisation
Stack et environnement. Le catalogue et son alimentation. L'extraction
et son interface fournisseur. L'orchestrateur. Le moteur de devis et ses
règles de quantité. Génération du PDF. Les deux canaux. Le tableau de
bord. Stratégie de test.

## Chapitre 5 — Résultats et évaluation
Le protocole des quatre dimensions. Résultats chiffrés. Analyse des
échecs d'extraction. Ce qui n'a pas pu être mesuré et pourquoi. Limites
du travail.
Perspectives : couverture d'autres types d'événements, puis extension à
d'autres domaines d'activité, l'hôtellerie étant le premier envisagé mais
le modèle de données n'y étant pas limité. Rattachement possible à
l'écosystème SEMA de Kaeyros sous le nom SEMA Estimate.

## Ce qui fera la différence
Le chapitre 5 et l'honnêteté sur les limites. Un rapport qui dit
précisément ce qu'il n'a pas pu mesurer et pourquoi vaut mieux qu'un
rapport qui affirme tout réussir. Le journal des décisions alimente
directement le chapitre 3 : chaque entrée est un arbitrage argumenté.