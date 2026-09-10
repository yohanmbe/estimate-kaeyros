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

Le tableau de bord affiche des indicateurs issus de requêtes sur la base :
nombre de demandes reçues, montant total estimé cumulé, répartition des
demandes par tranche d'invités. Aucun indicateur de conversion commerciale.
Raison : un taux de conversion supposerait de savoir quelles demandes ont
abouti à une vente, information que le produit ne détient pas puisqu'il
s'arrête à l'estimation (voir D08). Afficher un chiffre qu'on ne sait pas
justifier est aussi grave qu'un montant faux sur un devis.

Le montant moyen d'une estimation reste calculable
(src/indicateurs/devis.py::calculer_montant_moyen, toujours testé) mais
n'est plus affiché sur le tableau de bord : à effectif de demandes réduit,
il ne dit rien qu'un total et un compte ne disent déjà, et le gestionnaire
a demandé à ne plus le voir (2026-09-08).

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

## D27 — Le PDF porte les coordonnées du prospect et celles du tenant (2026-09-07)

generer_pdf_devis prend désormais un ProspectContexte en plus du tenant et
du besoin, et affiche un bloc « Demandé par » (nom, téléphone, email s'il
est connu) au même format que le récapitulatif de l'événement, ainsi que
Tenant.coordonnees dans l'en-tête, sous le nom de l'entreprise.
Raison : cohérent avec D26 (le prospect a sa propre table pour que le
commercial puisse le relancer) — un devis PDF sans les coordonnées de qui
l'a demandé ne servirait à rien pour cette relance une fois sorti du chat.
Tenant.coordonnees complète le PDF, dont l'en-tête porte déjà le nom du
tenant (D14) : le prospect qui reçoit le document doit pouvoir joindre
l'entreprise directement depuis le PDF.
Tenant.coordonnees transite maintenant par ConfigurationTenant
(src/catalogue/provisionnement.py) comme les autres champs du profil, au
lieu d'être posé après coup sur l'objet Tenant en dehors du chemin de
provisionnement partagé (voir D25) — ce contournement, découvert en
touchant ce code, faisait planter data/seed/seed.py avec un KeyError dès
le deuxième tenant (clés du dictionnaire de coordonnées désynchronisées
des slugs réels), corrigé au passage.

## D28 — La conversation écrit sa demande et son devis en base (2026-09-07)

Jusqu'ici rien n'écrivait jamais les tables demande et devis : le besoin vivait
dans st.session_state, le devis était recalculé à chaque rerun Streamlit et le
PDF produit à la volée. src/canaux/demande.py comble ce trou, à côté de
prospect.py : la demande s'ouvre dès que le prospect est connu (etat=en_cours),
son besoin est réenregistré à chaque tour, et le devis fige ses lignes à
l'émission avant de passer la demande à complete.
Raison : sans écriture, une conversation ne laissait aucune trace. Ni relance
commerciale possible alors que le cahier des charges pose que « sa demande
arrive qualifiée chez le commercial », ni aucun chiffre à afficher au
gestionnaire — trois des quatre indicateurs de D19 auraient affiché zéro à vie.
Contrepartie : une écriture par tour de conversation, et un devis émis même
quand le prospect ne télécharge pas son PDF.

## D29 — La demande est ouverte tôt, pas au moment du chiffrage (2026-09-07)

Elle est créée à l'enregistrement du prospect, avant la première question.
Raison : une conversation abandonnée en route est justement celle que le
commercial doit pouvoir rappeler. L'ouvrir au chiffrage n'aurait gardé que les
demandes déjà abouties. repartir_par_tranche_invites prévoyait déjà le cas
d'un besoin sans nombre_invites, qui n'entre alors dans aucune tranche.

## D30 — Un besoin modifié après émission produit un second devis (2026-09-07)

emettre_devis est idempotent sur le contenu : réémettre des lignes et un total
identiques renvoie le devis déjà enregistré, ce qui protège des reruns
Streamlit. Un besoin réellement modifié, en revanche, donne un nouveau devis ;
la demande, elle, reste unique.
Raison : les lignes émises ne se réécrivent pas (D11), et DONNEES.md définit le
montant total comme la somme des totaux des devis émis. Redéfinir un indicateur
pour dédoublonner ce cas de bord aurait coûté plus cher que de l'assumer.
Un rechargement de page (F5) perd la session Streamlit, donc le prospect et son
besoin : le formulaire réapparaît et une nouvelle demande est alors le
comportement correct, pas un doublon.

## D31 — Pas de date de validité sur un devis (2026-09-07)

devis.date_validite devient nullable et n'est jamais renseignée.
Raison : le produit s'arrête à l'estimation (D08). Une date de validité serait
un engagement commercial qu'il ne peut pas tenir, et la remplir d'office
(émission plus trente jours, par exemple) reviendrait à inventer une donnée
que personne n'a décidée — aussi grave qu'un montant faux. La colonne reste
déclarée pour le jour où une entreprise cliente voudra la porter.

## D32 — Retirer une prestation la désactive, sans jamais la supprimer (2026-09-07)

L'écran catalogue propose « Retirer » et non « Supprimer » : actif passe à
false, la ligne demeure.
Raison : Devis.lignes garde le ressource_id de chaque prestation facturée. Une
suppression dure rendrait un devis émis inauditable, ce qui contredirait D11.
Contrepartie : le catalogue du gestionnaire montre des prestations retirées que
le prospect ne voit plus ; l'écran les distingue par une pastille.

## D33 — Le cloisonnement est prouvé par les tests, pas seulement affirmé (2026-09-07)

tests/test_cloisonnement_tenant.py superpose quatre filets : le patron jumeau
(deux tenants, un seul interrogé) sur chaque fonction, un test d'accès direct
par identifiant pour chaque fonction adressée ainsi, un écouteur SQLAlchemy qui
lève dès qu'une requête touche une table métier sans tenant_id, et une garde de
signature exigeant tenant_id partout où une session circule.
Raison : « toute requête filtre sur tenant_id » est une règle qu'on ne peut pas
vérifier à l'œil sur un dépôt qui grandit. L'écouteur a d'ailleurs trouvé trois
requêtes non cloisonnées dès sa première exécution, dont un UPDATE de l'ORM qui
ne portait que la clé primaire.
Honnêteté du dispositif : l'écouteur ne voit que les requêtes qu'un test
exécute, et la garde de signature ne détecte pas un paramètre reçu puis ignoré.
L'oubli devient improbable, pas impossible.

## D34 — Aucune mise en cache Streamlit dans le tableau de bord (2026-09-07)

Pas de @st.cache_data ni @st.cache_resource dans dashboard/.
Raison : un cache dont la clé oublierait le tenant_id servirait les chiffres
d'une entreprise à une autre. C'est un argument de sécurité, pas de
performance : les requêtes portent sur quelques dizaines de lignes.

## D35 — Les demandes de démonstration vivent hors du provisionnement (2026-09-07)

data/seed/demonstration.py, lancé à la main sur un slug, crée des prospects,
des demandes et des devis de démonstration. provisionner_tenant (D25) n'y
touche pas.
Raison : provisionner sert aussi les vrais clients, et injecter des demandes
fictives dans l'espace d'une entreprise réelle serait une pollution. Le script
passe par le vrai chemin de production (enregistrement, ouverture, chiffrage
sur le catalogue réel, émission) : un total de démonstration est donc un total
que le moteur produirait, ce qui respecte D01 jusque dans la démo. Seules les
dates sont reculées après coup, pour que le sélecteur de période ait de la
matière.

## D36 — Tranches d'invités recalées sur le marché du mariage (2026-09-07)

Moins de 100, 100-250, 251-500, plus de 500, une borne haute n'appartenant
qu'à une seule tranche.
Raison : 300 invités sont courants à Yaoundé ; les tranches précédentes
(1-50, 51-150, 151-300, 301+) écrasaient la majorité des mariages dans la
dernière et n'apprenaient rien au gestionnaire.

## D37 — L'état « abandonnée » reste déclaré et non écrit (2026-09-07)

demande.etat ne prend que en_cours et complete dans les faits. Le filtre de
statut du tableau de bord ne propose donc que ces deux-là.
Raison : rien dans le produit ne sait distinguer une conversation abandonnée
d'une conversation en pause — il faudrait une règle de délai que personne n'a
décidée. Proposer un filtre qui ne peut jamais rien renvoyer vaudrait moins que
pas de filtre du tout. La valeur reste dans le modèle de données pour le jour
où cette règle sera posée.

## D38 — Le PDF ne présente plus le prospect à lui-même (2026-09-10)

Retrait du bloc « Demandé par » ajouté en D27 : le document est adressé au
prospect, il n'a pas besoin d'y lire son propre nom, téléphone et email.
generer_pdf_devis reperd son paramètre ProspectContexte, resté sans autre
usage dans le module. Dans l'en-tête, l'ordre devient nom du tenant, ses
coordonnées, puis la date et l'heure d'établissement — les coordonnées du
tenant suivent directement son nom, comme sur un papier à en-tête, plutôt
que d'être séparées par la date.
Raison : corrigé sur retour direct après usage du PDF généré. Les
coordonnées du prospect (D26) restent utiles ailleurs — la demande en base
et le tableau de bord du gestionnaire — seulement pas sur le document que
le prospect tient déjà entre les mains.

## D39 — Les salles se choisissent au plus proche, avec un devis sur mesure (2026-09-10)

La capacité ne fait plus que filtrer : elle classe. Les salles qui peuvent
accueillir tout le monde passent d'abord, de la plus juste à la plus large,
plafonnées à trois. Demander 300 places ne fait donc plus défiler les salles
de 800 tant qu'il existe des salles de 300. Quand aucune ne suffit, les plus
grandes du catalogue sont montrées quand même, avec un badge disant leur
capacité réelle. Dans les deux cas mal ajustés — rien d'assez grand, ou
seulement des salles démesurées — un choix supplémentaire apparaît : demander
une proposition sur mesure à l'entreprise.
Raison : l'ancien seuil dur produisait deux comportements absurdes observés en
test — 900 invités contre un catalogue plafonné à 500 émettait un devis *sans
aucune salle* et sans rien dire, et 50 invités faisaient défiler cinq salles de
100 sans hiérarchie. Le prospect doit voir ce que l'entreprise sait faire, même
quand ça ne correspond pas exactement.
Nuance D17 : le quartier trie toujours, mais en dernier, sur la liste déjà
réduite. Aucune salle n'est jamais écartée pour son quartier.
Contrepartie : une salle trop petite peut être choisie par le prospect. Elle
est signalée en rouge, mais rien ne l'en empêche — c'est son événement.

## D40 — Le LLM signale ses hypothèses, l'orchestrateur les fait confirmer (2026-09-10)

Le besoin porte trois nouveaux champs : dates_possibles, champs_a_confirmer
et champs_confirmes. L'extracteur y signale ce qu'il a *déduit* au lieu de lu
— une date relative résolue, un type d'événement compris à partir d'un mot
indirect. Une expression qui couvre plusieurs jours (« ce weekend ») remplit
dates_possibles et laisse la date vide. C'est ensuite decider_prochaine_etape,
du Python testé, qui décide de poser la question et le canal qui affiche les
boutons.
Raison : demander au LLM de poser lui-même la question violerait D01 et D04.
Lui faire signaler son incertitude reste de l'extraction : il décrit ce qu'il
a compris, y compris son doute. Le prospect voit le même résultat, mais la
décision est reproductible et testable sans appeler un modèle.
Une date que le modèle n'écrit pas au format canonique n'est jamais jetée :
elle part à confirmer. La perdre en silence reviendrait à la redemander comme
si le prospect n'avait rien dit.

## D41 — Le prospect a le dernier mot avant l'estimation (2026-09-10)

Une étape s'intercale entre les choix et le chiffrage : deux champs libres et
facultatifs, ce dont le prospect a besoin et qu'il n'a pas trouvé au catalogue,
et un mot pour l'entreprise. Ils sont stockés dans deux colonnes propres de la
table demande, jamais dans le JSON besoin, et s'affichent dans le détail de la
demande côté gestionnaire.
Raison : le catalogue ne couvrira jamais tout, et c'est justement ce qu'il ne
couvre pas qui intéresse le commercial. Le mettre dans le besoin mélangerait
le récit du prospect avec ce que l'extraction produit ; en colonnes, c'est
requêtable et ça ne se confond avec rien.
Contrepartie : un tour de plus avant de voir le montant. Passer outre sans
rien écrire reste possible en un clic.

## D42 — Une salle hors gabarit s'affiche seule, jamais en liste (2026-09-10)

Amende D39. La capacité borne désormais des deux côtés : une salle n'est
proposée que si elle peut accueillir tout le monde **et** ne dépasse pas deux
fois le nombre d'invités. Quand aucune salle du catalogue ne tient dans cette
fourchette, une seule est montrée — la plus petite qui suffise, ou la plus
grande du catalogue si aucune ne suffit — accompagnée du devis sur mesure et
d'un badge disant d'où elle sort (« la plus petite de notre catalogue »).
Raison : au premier test réel, un mariage de 50 invités s'est vu proposer des
salles de 400, 600 et 800 places, présentées comme trois options équivalentes.
Ce n'était pas un choix, c'était le catalogue entier. En montrer une seule dit
la vérité : l'entreprise n'a rien à cette taille, le vrai choix est entre cette
salle et un appel au commercial.
Contrepartie : le prospect voit moins d'options quand le catalogue est mal
ajusté. C'est précisément l'information utile.

## D43 — Corriger une valeur ne redemande que cette valeur (2026-09-10)

Le besoin porte `champ_en_correction`. Quand le prospect dit « non, je
corrige », ce champ est vidé et marqué : tant qu'il n'a pas été redonné, c'est
la seule chose qu'on lui demande, avant toute autre question ou confirmation.
Raison : au premier test, dire « ce n'est pas la date » déclenchait une
confirmation sur le type d'événement, puis la liste de tout ce qui manquait.
Le prospect avait été précis, la réponse ne l'était pas.

## D44 — Le jour nommé fait autorité sur la date produite (2026-09-10)

`parser_besoin` reçoit le message du prospect. Si celui-ci nomme un seul jour
de la semaine et que la date produite ne tombe pas ce jour-là, la date est
écartée et repart en correction. Un message citant plusieurs jours (« samedi
ou dimanche ») n'est pas tranchable et passe sans contrôle.
Raison : « le dernier samedi de décembre » a produit le jeudi 31 décembre,
proposé deux fois de suite. Le prompt le demande maintenant explicitement,
mais un prompt n'est pas une garantie : le garde-fou, lui, est déterministe et
testé sans appeler de modèle.
Contrepartie : le prospect doit redonner sa date. Mieux vaut ça que de lui
faire confirmer un jour qu'il vient de refuser.

## D45 — Un champ de l'événement non précisé est absent du PDF (2026-09-10)

Le récapitulatif « Votre événement » du PDF n'affiche plus « à préciser »
pour un champ resté vide (le quartier, en pratique — voir D17, jamais
obligatoire) : la ligne correspondante n'apparaît simplement pas.
Raison : sur ce document, contrairement au récapitulatif de la barre
latérale du chat en cours de conversation, il n'y a plus rien à réclamer au
prospect — le devis qu'il tient est déjà chiffré. Marquer un champ comme
manquant dessus suggérerait à tort qu'il doit encore fournir cette
information.

[Décisions suivantes à ajouter au fil du développement, avec la date.]
