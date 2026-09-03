ARCHITECTURE.md 

# Architecture — Estimate

## Les quatre couches

Le système est découpé en quatre morceaux qui ne se mélangent pas.

Le CANAL reçoit et renvoie des messages. Streamlit aujourd'hui, WhatsApp
demain. Il ne sait rien du métier : il transmet du texte et affiche des
réponses. C'est ce qui rend le second canal peu coûteux à ajouter.

L'EXTRACTEUR transforme une phrase en besoin structuré. C'est le seul
endroit où le LLM travaille, avec la reformulation. Il extrait, il ne
décide pas.

L'ORCHESTRATEUR conduit la conversation. Du code Python. Il regarde le
besoin, identifie ce qui manque, décide de la question suivante ou du
passage au chiffrage. Machine à états simple.

Le MOTEUR DE DEVIS interroge le catalogue et compose les lignes. Code
Python déterministe et testé. Même entrée, même sortie, toujours.

## Pourquoi ce découpage

Parce qu'il rend le système testable. On peut écrire quarante cas de test
sur le moteur de devis et vérifier les totaux au franc près. On peut
tester l'orchestrateur en lui donnant un besoin partiel et en vérifiant
quelle question il pose. Rien de tout ça n'est possible si le LLM pilote.

Parce qu'il rend le système auditable. Chaque montant du PDF remonte à
une ligne du catalogue. En cas de contestation, on sait d'où vient le
chiffre.

Parce qu'il coûte moins cher. Un appel au LLM par tour de conversation,
sur un petit modèle, au lieu d'un agent qui enchaîne les appels.

## Ce qu'on a écarté et pourquoi

Un agent à appels de fonctions, où le LLM orchestre lui-même : élégant,
mais comportement difficile à reproduire, coût par tour multiplié, et
diagnostic impossible quand ça dérape. Prématuré sur ce calendrier.

n8n ou un outil d'automatisation graphique : bon pour la plomberie
(recevoir un message, appeler une API), mauvais pour la logique métier.
Les règles de quantité et les cas limites deviennent illisibles en blocs,
et surtout ne se testent pas. Or ces tests sont le meilleur argument du
projet. Réserve : si l'intégration WhatsApp bloque plus de deux jours,
n8n redevient un raccourci acceptable pour ce seul point.

Du RAG sur les prix : jamais. Un montant issu d'une recherche sémantique
n'est ni auditable ni garanti. Le RAG aurait sa place sur des documents
descriptifs (conditions générales, descriptions de salles), c'est à dire
du texte vers du texte, pas du texte vers un chiffre. Hors périmètre v1.

## Flux d'une conversation

Le canal reçoit un message et le transmet avec l'identifiant de la
demande en cours.

L'extracteur lit le message et le besoin déjà connu, et renvoie le besoin
mis à jour. Un seul appel au LLM.

L'orchestrateur compare le besoin aux informations obligatoires (type,
date, ville, nombre d'invités, quartier). S'il en manque une, il produit
une question. Sinon il passe au chiffrage.

Au chiffrage, le moteur charge le modèle d'événement, filtre le catalogue
pour chaque catégorie attendue, calcule les quantités selon les règles,
compose les lignes et additionne.

Le PDF est généré, enregistré, et le canal l'envoie. La demande apparaît
dans le tableau de bord du tenant.

## Cas particuliers traités par le moteur

Aucune ressource ne correspond (capacité trop grande, quartier sans
salle) : le moteur le déclare. L'agent l'annonce et propose de
transmettre à un commercial. Il n'invente rien.

Plusieurs ressources correspondent : le moteur les renvoie toutes,
l'agent les présente, le prospect choisit.

Le total dépasse le budget déclaré : le moteur le signale. L'agent
l'annonce et propose de retirer des prestations ou d'élargir la
recherche. Il ne baisse aucun prix.

## Couche LLM

Tous les appels passent par une interface maison à deux méthodes :
extraire un besoin, reformuler un message. Le fournisseur est derrière.
Changer de fournisseur revient à écrire une nouvelle implémentation de
cette interface.

Un mock de cette interface, qui renvoie des réponses prédéfinies, permet
de tester toute l'application sans appeler le moindre modèle.

Fournisseur retenu : [À COMPLÉTER, viser un palier gratuit. Les offres
gratuites et leurs quotas changent souvent, à vérifier au démarrage.]

## Structure du dépôt

Les modules portent le nom de leur fonction, pas celui du produit.

src/canaux/        streamlit, whatsapp
src/extraction/    interface LLM, prompts, mock
src/orchestration/ machine à états, questions
src/moteur/        calcul du devis, règles de quantité
src/catalogue/     accès aux ressources
src/pdf/           génération du document
src/db/            modèles SQLAlchemy, migrations
dashboard/         interface gestionnaire Streamlit
tests/
data/seed/         jeu de démonstration