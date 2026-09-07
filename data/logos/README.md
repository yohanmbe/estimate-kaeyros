# Logos des tenants

Dossier fixe où src/canaux/tenant.py (`resoudre_chemin_logo`) va chercher le
logo d'un tenant, à partir du nom de fichier stocké dans `Tenant.logo` (voir
D24 dans DECISIONS.md). Il apparaît alors dans l'en-tête du PDF de devis
(voir D14).

## Pour activer le logo d'un tenant

1. Déposer le fichier ici (PNG ou JPG), par exemple `etoile.png`.
2. Renseigner ce même nom de fichier dans la colonne `logo` du tenant en
   base — actuellement fait dans `data/seed/seed.py`, en l'absence d'écran
   gestionnaire pour l'uploader (voir D18).

Un nom de fichier enregistré sans fichier correspondant ici ne fait pas
planter le PDF : l'en-tête se rabat simplement sur le nom du tenant seul.
