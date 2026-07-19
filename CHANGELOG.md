# Changelog

Historique des réalisations sur QualiCheck. Mis à jour par tout outil agentique utilisé (Claude Code, OpenCode...) — voir `CLAUDE.md` pour la règle d'usage.

Format d'entrée, une ligne par réalisation :

```
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

## 2026-07-19 — Claude Code (Part 2)

- **Étape 3 — Enrichissement (pipeline d'ingestion)** — voir `app/ingestion/enrichment.py`, `app/ingestion/llm_client.py`, `tests/unit/ingestion/test_enrichment.py`
  - Classe Pydantic `EnrichedRule` (schema.py) : extension de `RuleAggregation` avec champs enrichissement
  - Classe `EnrichedRules` (aggregation.py) : collection non-vide d'`EnrichedRule`
  - Classe `LLMClient` : client LangChain + Azure Kimi K2.6
    - Chargement prompt depuis `prompts/enrich_rule.md` (few-shot), remplacement manuel de placeholders (pas de `PromptTemplate.format()` — le prompt contient des accolades JSON littérales dans les exemples)
    - Retry logic : 3 tentatives, backoff exponentiel 2s/4s via `tenacity` (`wait_exponential(multiplier=2, min=2, max=8)`)
    - `JsonOutputParser` (langchain_core) pour parsing réponse LLM stricte
  - Fonction `enrich_rules()` : orchestration Rules → EnrichedRules
  - Logging : erreur critique (3 timeouts), synthèse succès
  - Tests unitaires : 6 tests (réussite, retry, échec après 3 tentatives, transformation collection, logging erreur/succès)
  - Dépendances : langchain>=0.1.0 (résolu 1.3.14), langchain-openai>=0.1.0, tenacity>=8.2.0
  - Convention : code anglais, docs/comments français
  - Renommage `agregation.py` → `aggregation.py` (noms de fichiers en anglais, cohérent avec le code)
  - Total : 22 tests unitaires ingestion passants (3 acquisition + 13 aggregation + 6 enrichment)

## 2026-07-19 — Claude Code

- **Étape 2 — Agrégation (pipeline d'ingestion)** — voir `app/ingestion/aggregation.py`, `tests/unit/ingestion/test_aggregation.py`
  - Classe Pydantic `RuleAggregation` (schema.py) : validation stricte (strings/listes non-vides)
  - Classe `Rules` : collection non-vide de règles agrégées
  - Fonction `aggregate_rules()` : transforme dicts acquis en Rules validée
  - Fail-fast sur validation (lève ValueError + log erreur)
  - Log synthèse : "X règles validées" si succès
  - Convention : code anglais (Rule, Rules, RuleAggregation), docs/comments français
  - Tests unitaires : 13 tests (Regle création, validation champs, collection, agrégation)
  - Propriété `regles` : alias rétrocompatibilité pour accès à la liste

---

## 2026-07-18 — Claude Code

- **Étape 1 — Acquisition (pipeline d'ingestion)** — voir `app/ingestion/acquisition.py`, `tests/unit/ingestion/test_acquisition.py`
  - `build_rule_url(slug)` : construction URL scraping
  - `fetch_api()` : récupération API Opquast (245 règles)
  - `scrape_rule(slug)` : scraping BeautifulSoup (solution + controle)
  - `acquire_rules()` : orchestration fetch + scrape par règle
  - Exceptions levées si données manquantes (fail-fast)
  - Logging centralisé dans `app/logging_config.py` (fichier uniquement)
  - Tests unitaires avec mocks (`@patch` requests.get)
  - Dépendance `beautifulsoup4` ajoutée à `pyproject.toml`
  - Variables `.env` : `OPQUAST_API_BASE_URL`, `OPQUAST_SITE_BASE_URL` — voir `.env.example`, `conception/2_ingestion/ingestion.md`
- Création de `app/ingestion/schema.py` : modèle Pydantic `RuleAcquisition` (id, number, intitule, objectifs, tags, phases, slug, solution, controle)
- Structure de tests : `tests/unit/ingestion/`, `tests/integration/ingestion/`, `tests/migration/` — voir `tests/conftest.py` pour fixtures partagées
- TODO : `TODO_PIPELINE_INGESTION.md` pour tracker les étapes restantes (agrégation, enrichissement, stockage, chunking, embedding, indexation, orchestration)

---

## 2026-07-18 — OpenCode

- Initialisation du dépôt Git — voir `.git/`
- Ajout du `.gitignore` (protection `.env`, Python, logs, éditeurs) — voir `.gitignore`
- Ajout du `.env.example` (variables PostgreSQL, valeurs vides) — voir `.env.example`
- Création du `.env` local (non versionné, valeurs de dev) — voir `.env`
- Ajout du `docker-compose.yml` : service `postgres` (pgvector/pgvector:pg17, port 8832, réseau `qualicheck`, volume `postgres_data`) — voir `docker-compose.yml`
- Ajout des docs de conception de la brique Docker/BDD — voir `docs/superpowers/specs/2026-07-18-docker-bdd-design.md`, `docs/superpowers/plans/2026-07-18-docker-bdd.md`
- Nommage explicite du conteneur PostgreSQL (`qualicheck-postgres`) — voir `docker-compose.yml`
- Ajout du `README.md` — voir `README.md`
- Ajout des fichiers de conception dans la branche feature (docs, annexes, maquettes, CLAUDE.md) — voir `conception/`, `app/CLAUDE.md`, `scripts/CLAUDE.md`
- Exclusion des fichiers de backup draw.io du versionnement — voir `.gitignore`
- Ajout de la règle "CHANGELOG mis à jour à chaque commit" dans `CLAUDE.md` — voir `CLAUDE.md`
- Ajout de la règle "pas de commit/push sans validation explicite" dans `CLAUDE.md` — voir `CLAUDE.md`

## 2026-07-18 — OpenCode

- Ajout des dépendances Python (sqlalchemy, alembic, psycopg2-binary, pgvector, python-dotenv, pytest, ruff) — voir `pyproject.toml`, `uv.lock`
- Création des modèles SQLAlchemy : `app/models/base.py`, `app/models/referentiel.py`, `app/models/metier.py`
- Configuration Alembic : `app/migration/alembic.ini`, `app/migration/env.py`
- Première migration Alembic (schéma complet + extension pgvector + index HNSW) — voir `app/migration/versions/0001_schema_initial.py`
- Point d'entrée CLI pour les migrations — voir `scripts/migration.py`
- Tests d'intégration de la migration (10 tests) — voir `tests/test_migration.py`
- Makefile : cibles `up`, `down`, `migration`, `downgrade`, `test` — voir `Makefile`
- Diagramme de flux de la migration — voir `docs/schemas/migration_flux.drawio`
- Specs et plan de la brique migration — voir `docs/superpowers/specs/2026-07-18-migration-design.md`, `docs/superpowers/plans/2026-07-18-migration.md`
- CI GitHub Actions : lint ruff + migration + tests sur push (hors main) — voir `.github/workflows/ci.yml`
- Configuration Ruff dans `pyproject.toml` (exclusion `conception/`)

---
