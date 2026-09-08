# Jeu de données de démonstration

Lancement (depuis la racine du projet, avec `DATABASE_URL` renseigné dans `.env`) :

```
uv run python data/seed/seed.py
```

Le script est idempotent : le relancer ne duplique rien.

## Contenu créé

Quatre tenants événementiels à Yaoundé, de gammes de prix différentes, pour
que les tests multi-locataires (isolation par tenant_id, tri par quartier,
filtrage par capacité/budget) aient de quoi être réalistes. Chacun a 15
ressources sur les 7 catégories (salle, mobilier, restauration, décoration,
sonorisation, personnel, logistique) et un modèle d'événement **Mariage**
(seul type d'événement en v1, voir CLAUDE.md).

| Tenant | Slug | Positionnement | Siège / Quartier | Salles (quartier / prix jour) |
|---|---|---|---|---|
| Événements Étoile | `etoile` | Intermédiaire/haut | 671234567, Bastos | Bastos 450k, Odza 250k, Mvan 600k |
| Yaoundé Prestige | `yaounde-prestige` | Haut de gamme | 677654321, Golf | Bastos 750k, Golf 900k, Warda 1,1M |
| Mariage Malin | `mariage-malin` | Économique | 650123456, Nkoabang | Nkoabang 120k, Ekounou 180k, Etoudi 280k |
| Nlongkak Réceptions | `nlongkak-receptions` | Milieu de gamme | 693456789, Nlongkak | Nlongkak 350k, Essos 280k, Mendong 500k |

## Identifiants de démonstration (tableau de bord)

| Tenant | Email | Mot de passe |
|---|---|---|
| Événements Étoile | `gestionnaire@etoile.com` | `passe` |
| Yaoundé Prestige | `gestionnaire@prestige.com` | `passe` |
| Mariage Malin | `gestionnaire@malin.com` | `passe` |
| Nlongkak Réceptions | `gestionnaire@nlongkak.com` | `passe` |

Usage local/démo uniquement. Les mots de passe sont hachés en base (scrypt) —
ces identifiants en clair ne vivent que dans ce fichier, pas ailleurs dans le
code.

Avant tout déploiement accessible publiquement, changer ces quatre mots de
passe : ce fichier devient public avec le dépôt, `passe` n'en est alors plus
un. `provisionner_tenant` (voir D25) ne touche jamais au mot de passe d'un
compte déjà créé, donc relancer `seed.py` ne suffit pas ; utiliser
`data/seed/changer_mot_de_passe.py` :

```
uv run python data/seed/changer_mot_de_passe.py gestionnaire@etoile.com
uv run python data/seed/changer_mot_de_passe.py gestionnaire@prestige.com
uv run python data/seed/changer_mot_de_passe.py gestionnaire@malin.com
uv run python data/seed/changer_mot_de_passe.py gestionnaire@nlongkak.com
```

Le nouveau mot de passe se saisit en masqué, jamais en argument de la
commande.
