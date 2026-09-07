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

## D16 — Le prospect est rattaché à une entreprise par le lien d'accès

Chaque tenant dispose de sa propre adresse d'accès au chat, sous la forme
d'un identifiant court dans l'URL. Le prospect n'a jamais à choisir une
entreprise dans une liste : il arrive sur le chat d'Événements Étoile
parce qu'Événements Étoile lui a donné ce lien, sur son site ou sa page
Facebook. Le canal lit cet identifiant au démarrage et charge le tenant
et son catalogue.
Raison : un produit vendu à des entreprises ne les met pas en
concurrence sur une place de marché. Chaque entreprise expose son propre
point d'entrée. Contrepartie : un lien invalide doit être traité
proprement, sinon la conversation démarre sans catalogue.

## D17 — La capacité filtre, le quartier trie

Une salle est retenue si sa capacité suffit au nombre d'invités. Le
quartier souhaité n'élimine aucune salle : il remonte en tête de liste
celles qui s'y trouvent.
Raison : la capacité est une contrainte physique, le quartier une
préférence. Un filtre dur sur le quartier renverrait une liste vide alors
que des salles conviennent à deux kilomètres. Contrepartie : le prospect
voit parfois des salles hors de son quartier, ce que l'affichage doit
rendre lisible.

## D18 — Authentification gestionnaire volontairement minimale en v1

Une table utilisateur rattachée au tenant, un mot de passe haché, une
connexion par identifiant et mot de passe. Pas de récupération de mot de
passe, pas de rôles multiples, pas de double authentification. Les
comptes sont créés dans le script de seed.
Raison : le cloisonnement entre entreprises doit être réel et
démontrable, mais l'authentification complète est un sujet à part entière
qui consommerait plusieurs jours sans rien apporter à la démonstration du
cœur du produit. Le durcissement figure dans les perspectives du rapport.
Le mot de passe est haché dès la v1, jamais stocké en clair, même en
démonstration.

## D19 — Les KPI se calculent, ils ne s'estiment pas

Le tableau de bord affiche quatre indicateurs issus de requêtes sur la
base : nombre de demandes reçues, montant total estimé cumulé, montant
moyen d'une estimation, répartition des demandes par tranche d'invités.
Aucun indicateur de conversion commerciale.
Raison : un taux de conversion supposerait de savoir quelles demandes ont
abouti à une vente, information que le produit ne détient pas puisqu'il
s'arrête à l'estimation (voir D08). Afficher un chiffre qu'on ne sait pas
justifier est aussi grave qu'un montant faux sur un devis.

## D20 — Options plafonnées à trois pour les catégories hors salle (2026-09-05)

Quand plusieurs ressources correspondent à une catégorie autre que la salle
(restauration, décoration, mobilier...), le moteur les trie par prix
croissant et n'en retient que trois. La salle reste régie par D17/D03 sans
aucune limite : sa capacité est une contrainte physique qui justifie de
montrer toutes les options restantes.
Raison : présenter le catalogue entier d'une catégorie dans une
conversation en langage naturel noierait le prospect sous les choix ;
trois options triées par prix restent lisibles dans un échange de chat.
Contrepartie : cette règle nuance D03 (« on les présente toutes ») pour les
catégories non contraintes par la capacité. Une évolution possible, non
retenue en v1 pour rester simple, serait de laisser le prospect indiquer un
prix maximum par catégorie afin d'affiner ce filtrage plutôt que de
plafonner arbitrairement à trois.

## D21 — Durée de l'événement obligatoire, jamais déduite (2026-09-05)

duree_jours rejoint la liste des informations obligatoires que
l'orchestrateur demande avant de passer au chiffrage (avec type, date,
ville, nombre d'invités, quartier). Le moteur ne lui applique aucune
valeur par défaut.
Raison : la durée détermine directement des quantités facturées (une
salle louée à la journée, du personnel par jour). Une valeur par défaut
silencieuse serait un montant partiellement deviné plutôt qu'extrait du
besoin réel, ce qui contredit D01.

## D20 — Fournisseur de LLM finalement Groq, pas Mistral(2026-09-06)

Décision initiale (voir D-choix fournisseur) : Mistral, pour la qualité
du français. En pratique, le palier gratuit Experiment de Mistral s'est
révélé inutilisable : limite de requêtes par minute fixée à 0, confirmée
par le support Mistral comme un comportement normal du mode gratuit sans
capacité réservée. Basculé vers Groq, dont le palier gratuit offre des
limites réellement exploitables au quotidien.
Raison : un fournisseur gratuit mais dont les appels échouent de façon
imprévisible ne permet ni de développer ni de démontrer le produit.
Ce changement a validé en pratique l'intérêt de l'interface d'isolation
du LLM (voir ARCHITECTURE.md, Couche LLM) : le code de Mistral a été
conservé sans être supprimé, une nouvelle implémentation a été ajoutée
à côté, et aucune autre couche du système n'a été modifiée.

## D22 — Une plage de dates explicite détermine la durée, une date seule non (2026-09-06)

Si le prospect donne une plage avec ses deux bornes (« du 12 au 14
décembre »), duree_jours est calculé à partir de cette plage par le LLM lors
de l'extraction (comptage inclusif : 12, 13, 14 décembre = 3 jours).
Raison : ce n'est pas une valeur par défaut, c'est un calcul sur une
information réellement fournie par le prospect, ce qui ne contredit pas D01.
Une date seule continue d'exiger une durée explicite : D21 reste inchangé
pour ce cas, qui reste le plus fréquent en pratique.

## D23 — Un réessai sur JSON tronqué à l'extraction (2026-09-06)

Découvert en testant D22 : le modèle produit parfois un JSON tronqué juste
avant l'accolade finale, rejeté par la validation de l'API. Rare (environ un
appel sur cinq dans le pire cas observé) et transitoire : une nouvelle
tentative immédiate suffit presque toujours. extraire_besoin (Groq et
Mistral) retente une fois avant d'abandonner et de renvoyer le besoin
inchangé.
Raison : sans ce réessai, un tour de conversation sur cinq perdait en
silence ce que le prospect venait de dire, qui devait le répéter. Mesuré
comme préexistant à D22, pas causé par l'allongement du prompt (huit essais
sur chaque version du prompt, aucun échec des deux côtés).

## D24 — Tenant.logo stocke un nom de fichier, résolu dans un dossier fixe (2026-09-07)

Tenant.logo contient uniquement un nom de fichier (par exemple « etoile.png »),
jamais un chemin absolu ni un chemin relatif au répertoire de travail.
src/canaux/tenant.py le résout dans data/logos/ au moment de construire le
TenantContexte, avant que le PDF (voir D14) ou tout autre canal n'en ait besoin.
Un nom introuvable donne un logo absent, jamais une erreur.
Raison : un chemin absolu ne survit pas à un changement de machine ou de
déploiement ; un chemin relatif dépend de l'endroit d'où Streamlit est lancé,
ce qui n'est pas garanti stable. Un dossier fixe partagé par tout le code
règle les deux problèmes d'un coup, sur le même principe que le logo de
repli de la barre latérale (src/canaux/assets/, voir _logo_marque).
Contrepartie : déposer le fichier dans data/logos/ ne suffit pas seul, il faut
aussi que Tenant.logo porte le nom exact du fichier — pour l'instant fait dans
data/seed/seed.py, en l'absence d'écran gestionnaire pour l'uploader (voir D18).

## D25 — Un provisionnement de tenant partagé entre démo et vrais clients (2026-09-07)

src/catalogue/provisionnement.py porte la logique de création ou mise à jour
d'un tenant complet (profil, catalogue, modèle Mariage, gestionnaire),
appelée à la fois par data/seed/seed.py (le tenant de démonstration, codé en
dur) et par data/seed/ajouter_tenant.py (un vrai client, décrit dans un
fichier JSON hors du dépôt, voir data/clients/README.md). Aucun écran
gestionnaire pour créer un tenant soi-même : ça reste un script lancé par
l'opérateur (voir D18).
Raison : chaque entreprise a son propre catalogue et ses propres prix, qui
n'ont rien à faire codés en dur dans une source versionnée. Dupliquer la
logique de création entre deux scripts aurait fait diverger à la première
correction (voir la mise à jour d'un tenant déjà existant, elle-même corrigée
après avoir découvert que get_or_create_tenant ne mettait pas ses champs à
jour). Un fichier JSON par client, gitignoré sauf son exemple, garde les
données commerciales hors du code sans exiger un écran d'administration
hors périmètre v1.

## D26 — Le prospect a sa propre table, distincte du besoin (2026-09-07)

Ajout de la table prospect (nom, telephone obligatoires, email et
consentement_contact) et remplacement de demande.identifiant_prospect
(une chaîne libre, jamais lue ni écrite par le code) par
demande.prospect_id, une vraie clé étrangère.
Raison : le besoin décrit l'événement, pas qui le demande. Sans
coordonnées structurées, une demande qui n'aboutit pas ne peut jamais
être relancée par le commercial, alors que le cahier des charges pose
justement que « sa demande arrive qualifiée chez le commercial ».
Cohérent avec D02 (objets concrets nommés plutôt que chaînes vagues).
Pas de déduplication par téléphone en v1 : chaque demande crée une
nouvelle ligne prospect, pas de recherche-ou-création. Le rapprochement
entre plusieurs demandes d'un même prospect n'est pas un besoin exprimé
pour cette version.
Portée volontairement limitée au modèle de données : le formulaire de
saisie dans le chat Streamlit et la persistance d'une ligne demande par
conversation (qui n'existe pas encore, la conversation vivant entièrement
en st.session_state) restent à faire séparément.

[Décisions suivantes à ajouter au fil du développement, avec la date.]
