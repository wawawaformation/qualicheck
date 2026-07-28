# QualiCheck

Application web d'aide à l'audit qualité web basée sur le référentiel **Opquast** (245 règles). Les agents LLM assistent l'auditeur à chaque étape — génération de constats, dialogue, question libre — sans jamais se substituer à sa décision finale.

Projet fil rouge de la certification **RNCP37827 — Développeur IA agentique**, réalisé avec le soutien d'Élie Sloïm (fondateur d'Opquast).

---

## Fonctionnalités

- **US0 — Ingestion** : import des 245 règles Opquast (API + scraping), enrichissement par agent LLM, vectorisation et indexation pgvector
- **US1 — Audit assisté** : crawl léger, sélection de pages et de règles, génération de constats, dialogue et validation humaine, rapport final
- **US2 — Question libre** : RAG sémantique pur sur une URL ou une capture d'écran, guardrails, mémoire de session

---

## Stack technique

| Composant | Technologie |
| --- | --- |
| Backend | FastAPI (Python) |
| Frontend | Vue.js |
| Base de données | PostgreSQL + pgvector (HNSW, 1536 dim) |
| Migrations | Alembic |
| Gestion des dépendances | uv |
| LLM (dev) | Kimi K2.6, gpt-5.4, gpt-5.4-mini via Azure |
| LLM (prod) | Apertus-70B, Mistral Small via Infomaniak |
| Embedding (actuel) | text-embedding-3-small via Azure |
| Embedding (cible) | BGE Multilingual Gemma2 via Infomaniak (quand disponible) |
| Déploiement | Docker + docker-compose |

---

## Lancer le projet

### Prérequis

- Docker + docker-compose
- Python 3.11+ avec [uv](https://github.com/astral-sh/uv)
- Un fichier `.env` à la racine (voir `.env.example`)

### 1. Démarrer la base de données

```bash
docker compose up -d
```

PostgreSQL + pgvector est accessible sur `localhost:8832`.

### 2. Appliquer les migrations

```bash
uv run python scripts/migration.py
```

### 3. Lancer l'ingestion

```bash
uv run python scripts/ingestion.py
```

---

## Architecture IA

QualiCheck mobilise trois usages distincts du RAG :

| US | Mode | Justification |
| --- | --- | --- |
| US1 — génération | SQL déterministe | Règles connues, sélectionnées par l'auditeur |
| US1 — dialogue | SQL déterministe | Contexte d'audit connu, constats posés |
| US2 — question libre | RAG sémantique pur | Pas de présélection, pgvector cherche les règles pertinentes |

La **feedback loop** collecte les validations et rejets des auditeurs (`validation_humaine`, `feedback_auditeur`) pour alimenter une ré-ingestion ciblée en post-MVP.

---

## Positionnement éthique

- **Souveraineté numérique** : production hébergée chez Infomaniak (Suisse), hors Cloud Act américain
- **Éco-conception** : embedding léger (33M paramètres), pas de base vectorielle externe, infrastructure 100% renouvelable
- **IA non décisionnaire** : l'agent propose, l'auditeur valide — toujours

---

## Structure du projet

```text
app/            # Domaine métier (models, migration, ingestion)
conception/     # Documents de conception (specs, MCD, flux)
scripts/        # Points d'entrée CLI (migration.py, ingestion.py)
logs/           # Logs d'exécution
docker-compose.yml
```

---

## Licence

Le référentiel Opquast est diffusé sous **[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr)** — attribution et partage à l'identique. Cette licence s'applique sans autorisation préalable, et le partage à l'identique étant viral, elle s'étend au jeu de données enrichi que produit ce projet.

Attribution : « Référentiel Opquast - Qualité Numérique » par Opquast, utilisé sous licence CC BY-SA 4.0.

Ce projet pédagogique bénéficie en outre du **soutien d'Élie Sloïm** (fondateur d'Opquast), qui légitime l'usage expérimental du référentiel et du serveur MCP dans le cadre de la certification — ce que la licence seule ne couvre pas.

La licence du code du projet et celle des étages applicatif et présentation ne sont pas encore arrêtées. Voir `docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`.
