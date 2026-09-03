DECISIONS.md

# Journal des décisions — Estimate

Une ligne par arbitrage tranché, avec sa raison. Évite de rejouer les
mêmes débats et alimente directement le rapport.

## D01 — Le LLM n'écrit jamais un montant
Le LLM extrait le besoin et reformule. Tout chiffre vient du catalogue
via un calcul Python testé. Raison : un devis doit être garanti et
auditable. Contrepartie : la conversation est moins libre qu'avec un
agent autonome, mais elle est reproductible.

## D02 — Ressources nommées plutôt que catégories abstraites
Le catalogue contient « Salle Étoile, Bastos, 300 places, 500 000 » et
non « salle 300 places : 500 000 ». Raison : c'est ce qui permet au prix
de varier selon le lieu et le prestataire sans règle artificielle.

## D03 — Options présentées, pas choix imposé
Quand plusieurs ressources correspondent, on les présente toutes. Raison :
choisir sa salle est justement la décision que l'organisateur veut
prendre. Contrepartie : un tour de conversation de plus.

## D04 — Orchestration par machine à états, pas par le LLM
Raison : testable, coût maîtrisé, diagnostic possible. Contrepartie :
moins impressionnant en démonstration qu'un agent libre.

## D05 — Multi-locataires dès la première table
Colonne tenant_id partout, filtrage systématique. Raison : rétrofitter
un cloisonnement revient à réécrire l'application.

## D06 — Streamlit avant WhatsApp
Raison : WhatsApp est de la configuration à durée imprévisible. Commencer
par là risque de laisser le projet sans démonstration. L'architecture en
couches rend l'ordre indifférent.

## D07 — Mariage seulement en v1
Raison : un type traité à fond vaut mieux que trois bâclés en deux
semaines. Le mécanisme des modèles d'événement est démontré avec un seul.

## D08 — Le produit s'arrête à l'estimation
La disponibilité, la réservation, la facturation et le suivi commercial
restent chez l'entreprise cliente. Raison : elle a déjà ses processus et
ses outils pour cela ; un agent qui empiéterait dessus entrerait en
conflit avec l'existant et compliquerait chaque installation. Ce n'est
pas une limite de version, c'est la frontière du produit.

## D09 — Pas d'entraînement de modèle
Raison : demande des données annotées inexistantes, du matériel plus
cher que des appels d'API, et des semaines de travail pour un résultat
inférieur. La contrainte de coût nul se règle par un petit modèle sur un
palier gratuit.

## D10 — Montants en entiers FCFA
Raison : les flottants produisent des erreurs d'arrondi visibles sur un
total.

## D11 — Devis figé à l'émission
Les lignes et les montants sont enregistrés, pas recalculés. Raison : un
devis est un document daté, pas un calcul rejoué.

## D12 — Pas de validation humaine avant envoi
Confirmé par le responsable. Compensé par la mention d'estimation
indicative non contractuelle et par l'apparition de chaque demande dans
le tableau de bord. Raison : le prospect est servi immédiatement,
l'entreprise garde la main.

## D13 — Nom du produit : Estimate
Nom neutre sur le secteur, ce qui préserve l'extension à l'hôtellerie.
Rattachement possible à l'écosystème SEMA de Kaeyros sous le nom
SEMA Estimate si le produit est retenu. Le code n'utilise pas ce nom
pour ses modules, qui sont nommés par leur fonction.

## D14 — Le PDF porte l'identité de l'entreprise cliente
En-tête au nom et au logo du tenant, pas au nom du produit. Raison : le
prospect achète à l'entreprise événementielle, pas à Kaeyros. Un outil
vendu ne s'affiche pas à la place de son utilisateur.

## D15 — Extension multi-domaines, pas seulement l'hôtellerie
Le modèle de données décrit des ressources génériques (nom, catégorie,
unité de facturation, prix, attributs souples). Rien n'y est propre à
l'événementiel. L'hôtellerie est le premier domaine envisagé parce que
le responsable l'a cité, mais le mécanisme vaut pour tout métier qui
chiffre des prestations à partir d'un catalogue.

[Décisions suivantes à ajouter au fil du développement, avec la date.]