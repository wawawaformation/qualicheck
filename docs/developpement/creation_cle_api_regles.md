# Créer une nouvelle clé API — API données (`/regles`)

Procédure pour déclarer un nouveau client autorisé au `PATCH /regles/{numero}`
(annotation de revue humaine). Contexte et choix d'architecture :
`docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md`.

À refaire à l'identique pour dev (local) et pour staging — les deux
environnements déclarent les mêmes clients.

**Raccourci** : `scripts/creer_cle_api_regles.py <nom-client>` automatise les
étapes 1 à 5 (génère le jeton, modifie les 4 fichiers, crée le secret GitHub).
Reste manuel après : relire les diffs, redémarrer l'API locale, committer et
merger jusqu'à `staging`. Le détail ci-dessous reste la référence en cas de
problème ou pour comprendre ce que fait le script.

## 1. Choisir un nom de client et sa variable d'environnement

- Nom de client (`nom` dans le manifeste) : identifie la personne, en
  kebab-case (ex. `jean-dupont`).
- Variable d'environnement associée : `FASTAPI_API_KEY_<NOM_EN_MAJUSCULES>`
  (ex. `FASTAPI_API_KEY_JEAN_DUPONT`) — même convention que les clients
  existants (`dev`, `elie-sloim`, `david-legrand`, `formateur`).

## 2. Générer un jeton fort

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Un jeton par client, jamais réutilisé, jamais loggé (voir
`app/api_regles/auth.py`).

## 3. Déclarer le client dans le manifeste

Ajouter une entrée dans `clients:` de `app/api_regles/manifest.yml` :

```yaml
clients:
  - nom: dev
    env_var_token: FASTAPI_API_KEY
  # ...
  - nom: jean-dupont
    env_var_token: FASTAPI_API_KEY_JEAN_DUPONT
```

Ce fichier est commun à dev et staging (versionné) — une seule modification.

## 4. Dev (local)

1. Documenter la variable dans `.env.example` (valeur vide, avec commentaire) :

   ```
   FASTAPI_API_KEY_JEAN_DUPONT=  # secret : token Bearer du client "jean-dupont"
   ```

2. Ajouter la vraie valeur (générée à l'étape 2) dans `.env` local (non
   versionné).
3. Redémarrer l'API pour que `config.clients_tokens()` relise l'environnement :
   - via `make api-regles` : `Ctrl+C` puis relancer.
   - via Docker (`make up`) : `docker compose restart api-regles`.

`config.clients_tokens()` lève `RuntimeError` au démarrage si une variable
déclarée dans le manifeste est absente de l'environnement — un oubli est
donc bloquant immédiatement, pas silencieux.

## 5. Staging

Deux endroits à modifier, tous deux nécessaires :

1. **Secret GitHub** : Settings → Environments → `staging` → New environment
   secret. Nom `FASTAPI_API_KEY_JEAN_DUPONT`, valeur = le jeton généré à
   l'étape 2 (le même que dans le `.env` local, ou un jeton différent si ce
   client ne doit pas avoir accès aux deux environnements).
2. **Workflow de déploiement** : `.github/workflows/cd-staging.yml` écrit le
   `.env` du serveur à partir des secrets — il énumère les variables
   explicitement, une ligne par client. Ajouter :

   ```yaml
   FASTAPI_API_KEY_JEAN_DUPONT=${{ secrets.FASTAPI_API_KEY_JEAN_DUPONT }}
   ```

   dans l'étape « Écrire `.env` depuis les secrets de l'environnement
   staging », à la suite des lignes `FASTAPI_API_KEY_*` existantes.

3. Committer ce changement de workflow, merger jusqu'à `staging` (le push
   sur cette branche déclenche `cd-staging.yml`, qui redémarre l'API avec le
   nouveau `.env`).

Sans l'étape 2 (modification du workflow), le secret existerait côté GitHub
mais ne serait jamais écrit dans le `.env` du serveur — le client resterait
non authentifiable en staging malgré un secret déclaré.

## 6. Vérifier

```bash
# Dev
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH http://localhost:8880/regles/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jeton généré>" \
  -d '{"review_status":null}'

# Staging
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH https://regles.qualicheck.koabana.fr/regles/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jeton généré>" \
  -d '{"review_status":null}'
```

`200` attendu dans les deux cas (`review_status: null` est un no-op inoffensif
sur une règle non revue — ne modifie rien si elle l'est déjà).

## Révoquer un client

Opération symétrique : retirer l'entrée dans `manifest.yml`, la ligne dans
`cd-staging.yml`, la variable dans `.env`/`.env.example`, et supprimer le
secret GitHub correspondant. Le jeton révoqué renvoie alors `401` partout.
