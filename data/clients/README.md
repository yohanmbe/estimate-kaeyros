# Ajouter un vrai client

Chaque client a son propre catalogue et ses propres prix : rien de tout ça
ne va dans le code source. `exemple.json` est le seul fichier de ce dossier
suivi par git — les vraies configurations restent locales (voir
.gitignore : `data/clients/*.json` sauf `exemple.json`), puisqu'elles portent
un mot de passe en clair au premier lancement.

## Marche à suivre

1. Copier `exemple.json` vers un nouveau fichier, par exemple
   `mon-client.json`, et remplir ses champs :
   - `nom`, `slug` (utilisé dans l'URL du chat : `?slug=...`), `ville`
   - `logo` : nom de fichier attendu dans `data/logos/` (voir cette README
     et D24 dans DECISIONS.md) — omettre le champ si le client n'a pas
     encore fourni de logo, le PDF se rabat alors sur son nom seul
   - `coordonnees` : téléphone et quartier du siège, affichés dans l'en-tête
     du PDF (voir D14) — omettre le champ tant qu'ils ne sont pas connus
   - `ressources` : le catalogue du client (une entrée par prestation)
   - `modele_mariage` : les catégories attendues pour un mariage chez ce
     client, et comment leur quantité se calcule (voir DONNEES.md)
   - `gestionnaire` : le compte du tableau de bord de ce client
2. Déposer son logo dans `data/logos/` sous le nom indiqué, s'il est prêt.
3. Lancer :
   ```
   uv run python data/seed/ajouter_tenant.py data/clients/mon-client.json
   ```
   Relancer la commande après une modification du fichier met à jour le
   tenant : rien n'est dupliqué (voir src/catalogue/provisionnement.py).
4. Communiquer au client l'adresse de son chat (`?slug=...`) et les
   identifiants de son gestionnaire affichés par le script, puis retirer le
   mot de passe en clair du fichier JSON.
