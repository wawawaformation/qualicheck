# Plan d'implémentation — Renommage et nettoyage des variables d'environnement API

2026-09-20

## Contexte

Le préfixe `FASTAPI_*` dans `.env` est générique et ne dit pas à quelle API
il sert. Il désigne en réalité `api_regles` (et son équivalent préprod). À
l'arrivée de `api_business` (partagée US1/US2, `conception/3_autre_us/en_commun.md`),
il faut des noms explicites et cohérents par service.

## Objectif

Rendre explicite la provenance des variables liées aux APIs, supprimer
l'URL en dur dans le client Vue.js, et supprimer le workflow GitHub
obsolète.

## Variables renommées

| Ancienne variable | Nouvelle variable | Usage |
| --- | --- | --- |
| `FASTAPI_URL_PROD` | `API_REGLES_URL_PREPROD` | URL préprod de `api_regles` |
| `API_REGLES_URL` | `API_REGLES_URL_DEV` | URL dev de `api_regles` (`http://localhost:8880`) |
| `FASTAPI_API_KEY` | `API_REGLES_TOKEN_DEV` | jeton client "dev" de `api_regles` |
| `FASTAPI_API_KEY_ELIE` | `API_REGLES_TOKEN_ELIE` | jeton client "elie-sloim" |
| `FASTAPI_API_KEY_DAVID` | `API_REGLES_TOKEN_DAVID` | jeton client "david-legrand" |
| `FASTAPI_API_KEY_FORMATEUR` | `API_REGLES_TOKEN_FORMATEUR` | jeton client "formateur" |

Variables réservées pour `api_business` (sans valeur réelle pour l'instant) :

- `API_BUSINESS_URL_DEV=http://localhost:8882`
- `API_BUSINESS_URL_PREPROD=https://api.qualicheck.koabana.fr`
- `API_BUSINESS_TOKEN_*` laissées vides (authentification définie dans les cartes suivantes)

## Fichiers à modifier

| Fichier | Changement |
| --- | --- |
| `.env` | Renommer les variables réelles + ajouter `API_BUSINESS_*` réservées |
| `.env.example` | Idem, avec placeholders |
| `app/api_regles/config.yml` | `env_var_token: FASTAPI_API_KEY*` → `API_REGLES_TOKEN_*` |
| `app/agent_us2/config.yml` | `env_var_url: API_REGLES_URL` → `API_REGLES_URL_DEV` ; commentaire mis à jour |
| `app/agent_us2/main.py` | `service_name="qualicheck-agent-us2"` → `"qualicheck-api-business"` |
| `clients/regles_api_client/src/apiServer.js` | Supprimer l'URL en dur, utiliser variable d'environnement Vite |
| `clients/regles_api_client/.env` / `.env.example` | Ajouter l'URL dev et préprod si absente |
| `scripts/creer_cle_api_regles.py` | Préfixe `FASTAPI_API_KEY` → `API_REGLES_TOKEN` ; vérifier target manifest |
| `.gitea/workflows/cd-staging.yml` | `secrets.FASTAPI_API_KEY*` → `secrets.API_REGLES_TOKEN_*` |
| `.github/workflows/cd-staging.yml` | Idem |
| `archive_github/.github/workflows/cd-staging.yml` | Supprimer |
| `Makefile` | Vérifier qu'aucune variable FASTAPI n'est utilisée |
| `docs/developpement/creation_cle_api_regles.md` | Mettre à jour les noms de variables |
| `docs/developpement/deploiement_staging.md` | Vérifier et mettre à jour si besoin |
| `CHANGELOG.md` | Tracer le renommage, le service_name, la suppression archive |

## Ordre d'exécution

1. Modifier `.env.example` (template, sans secret).
2. Modifier `.env` (vrai fichier, avec secrets).
3. Modifier `app/api_regles/config.yml`.
4. Modifier `app/agent_us2/config.yml`.
5. Modifier `app/agent_us2/main.py`.
6. Modifier `scripts/creer_cle_api_regles.py`.
7. Modifier les workflows CD (`.gitea/`, `.github/`).
8. Supprimer `archive_github/.github/workflows/cd-staging.yml`.
9. Modifier `clients/regles_api_client/src/apiServer.js` et son `.env`.
10. Mettre à jour la documentation.
11. Vérifier (grep, tests, ruff, build client).
12. Tracer dans `CHANGELOG.md`.

## Vérifications prévues

- `grep -R "FASTAPI_"` vide sauf `CHANGELOG.md` (historique).
- `grep -R "\bAPI_REGLES_URL\b"` (sans suffixe) vide.
- `make api-regles` démarre correctement.
- `uv run pytest tests/unit/api_regles tests/unit/agent_us2` passe.
- `uv run ruff check .` vert.
- Client Vue.js build OK.
