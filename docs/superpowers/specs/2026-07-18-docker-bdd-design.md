# Design — Docker + BDD

**Date :** 2026-07-18  
**Phase :** feature (avant dev et main)  
**Périmètre :** infrastructure Docker et base de données PostgreSQL + pgvector

---

## Contexte

Première brique technique de QualiCheck. Pose les fondations pour que les scripts `migration.py` et `ingestion.py` aient une base opérationnelle.

Les migrations et l'ingestion sont lancées **manuellement depuis l'hôte** (`uv run python scripts/...`) — pas de conteneurs éphémères pour ces étapes, conformément à `bdd.md` (déclenchement manuel et maîtrisé).

---

## Fichiers créés

```
.gitignore
.env               ← jamais versionné
.env.example       ← versionné, valeurs vides
docker-compose.yml
```

---

## docker-compose.yml

### Service `postgres`

| Paramètre | Valeur |
|---|---|
| Image | `pgvector/pgvector:pg17` |
| Port hôte | `8832` |
| Port interne | `5432` |
| Volume | `postgres_data` (nommé, persistant) |
| Réseau | `qualicheck` (bridge) |
| Variables d'env | lues depuis `.env` |

L'image `pgvector/pgvector:pg17` intègre l'extension pgvector nativement — l'activation (`CREATE EXTENSION vector`) reste à la charge de la première migration Alembic, mais l'installation système est déjà présente dans l'image.

### Réseau

Réseau bridge nommé `qualicheck`, partagé entre tous les futurs services du projet. Isolation claire par rapport au réseau Docker par défaut.

### Convention de ports

Tous les services QualiCheck sont exposés sur `88xx`. PostgreSQL : `8832` (suffixe `32` ← port natif `5432`).

---

## Variables d'environnement

Fichier unique `.env` à la racine, partagé par docker-compose et les scripts Python.

| Variable | Valeur par défaut | Usage |
|---|---|---|
| `POSTGRES_USER` | `qualicheck` | docker-compose + Alembic + ingestion |
| `POSTGRES_PASSWORD` | voir `.env.example` | docker-compose + Alembic + ingestion |
| `POSTGRES_DB` | `qualicheck` | docker-compose + Alembic + ingestion |
| `POSTGRES_HOST` | `localhost` | Alembic + ingestion (connexion depuis l'hôte) |
| `POSTGRES_PORT` | `8832` | Alembic + ingestion |

`.env.example` contient les mêmes clés avec des valeurs vides — document de référence versionné pour les nouveaux contributeurs.

---

## .gitignore

Couvre :
- `.env` (jamais versionné)
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.venv/`
- `logs/` (logs d'exécution des scripts)
- Fichiers d'éditeur courants (`.idea/`, `.vscode/`, `*.swp`)

---

## Ce que ce design ne couvre pas

- Conteneur pour les migrations ou l'ingestion (hors périmètre, déclenchement manuel)
- Service FastAPI ou Vue.js (non conçus à ce stade)
- CI/CD (prévu ultérieurement, ne doit pas contraindre ce design)
