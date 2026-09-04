# Jeu de données de démonstration

Lancement (depuis la racine du projet, avec `DATABASE_URL` renseigné dans `.env`) :

```
uv run python data/seed/seed.py
```

Le script est idempotent : le relancer ne duplique rien.

## Contenu créé

- Tenant **Événements Étoile** (Yaoundé), slug `etoile`.
- 15 ressources réparties sur les 7 catégories (salle, mobilier, restauration,
  décoration, sonorisation, personnel, logistique).
- Modèle d'événement **Mariage** avec ses lignes par défaut.

## Identifiants de démonstration (tableau de bord)

- Email : `gestionnaire@etoile-events.cm`
- Mot de passe : `Etoile-Demo-2026`

Usage local/démo uniquement. Le mot de passe est haché en base (scrypt) —
ces identifiants en clair ne vivent que dans ce fichier, pas ailleurs dans le
code.
