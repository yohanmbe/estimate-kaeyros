CAHIER-DES-CHARGES.md

# Cahier des charges — Estimate

## Le besoin

Une entreprise événementielle reçoit des demandes de prospects par
téléphone et par messagerie. Chiffrer une demande demande du temps à un
commercial : comprendre le besoin, chercher les prix, composer le devis.
Beaucoup de demandes ne sont jamais chiffrées, ou trop tard.

Estimate automatise la première étape. Le prospect décrit son événement,
obtient une estimation immédiate, et sa demande arrive qualifiée chez le
commercial.

## Ce que fait le produit

Un prospect converse avec l'agent, en français, sur une interface web
(Streamlit) ou sur WhatsApp. L'agent recueille le besoin par étapes,
propose les ressources du catalogue qui correspondent, compose une
estimation chiffrée et l'envoie en PDF.

L'entreprise cliente dispose d'un tableau de bord où elle saisit son
catalogue (salles, prestations, prix) et consulte les demandes reçues.



## La frontière du produit

Estimate produit une estimation, rien de plus. La disponibilité des
salles, la réservation, la facturation et le suivi commercial
appartiennent à l'entreprise cliente et à ses propres outils. Ce n'est
pas une limite de la v1, c'est le périmètre du produit.

Ne sont pas non plus couverts en v1 : la comparaison de plusieurs
fournisseurs pour une même prestation, le prix du catalogue faisant foi ;
les types d'événements autres que le mariage ; les secteurs autres que
l'événementiel.

Le devis produit est une estimation indicative, non contractuelle,
valable \[À COMPLÉTER : nombre de jours, proposition 15]. Le PDF précise
que les prestations restent à confirmer par l'entreprise.



## Utilisateurs

Le prospect : particulier ou entreprise qui organise un événement. Il ne
connaît pas les prix du marché, il exprime un besoin en langage courant,
souvent incomplet.

Le gestionnaire : employé de l'entreprise cliente. Il saisit le catalogue
et reprend les demandes reçues. Il n'est pas technique.

## Critères d'acceptation

Un prospect qui décrit un mariage en langage naturel obtient un PDF
chiffré sans intervention humaine.

Tout montant du PDF est traçable jusqu'à une ligne du catalogue. Aucun
montant ne provient du LLM.

Le moteur de devis passe une suite de tests automatisés couvrant les cas
nominaux et les cas limites (budget insuffisant, capacité introuvable,
information manquante).

Le gestionnaire peut ajouter une salle et une prestation depuis le
tableau de bord, et cette modification est prise en compte au devis
suivant.

Chaque devis conserve les montants tels qu'ils étaient à son émission,
même si les prix changent ensuite.

## Calendrier

Semaine 1 : modèle de données, catalogue, moteur de devis testé,
extraction du besoin, conversation Streamlit, génération PDF.
Semaine 2 : tableau de bord gestionnaire, canal WhatsApp si possible,
campagne d'évaluation, rédaction.

Date de démonstration : \[À COMPLÉTER]
Date de rendu du rapport : \[À COMPLÉTER]

## Ce que le responsable doit pouvoir décider après la démonstration

Si le produit vaut d'être poussé jusqu'à une version commercialisable.
Quel effort représente l'extension à un autre domaine d'activité.
Quelles fonctionnalités manquent pour un premier client réel.



Le prospect accède au chat d'une entreprise donnée par un lien qui lui

est propre. Il ne choisit jamais l'entreprise dans une liste.



Une salle est proposée si sa capacité couvre le nombre d'invités. Les

salles du quartier souhaité apparaissent en premier, les autres restent

proposées.



Un gestionnaire accède à son tableau de bord après s'être authentifié par

email et mot de passe. Il ne voit que les données de son entreprise.



Le tableau de bord affiche quatre indicateurs sur une période choisie :

nombre de demandes, montant total estimé, montant moyen, répartition par

tranche d'invités.

