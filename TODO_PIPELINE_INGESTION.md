# Pipeline d'Ingestion — État d'avancement

Référence : `conception/2_ingestion/ingestion.md`

## Étapes du pipeline

- [x] **Étape 1 — Acquisition**
  - [x] `build_rule_url(slug)` — construction URL scraping
  - [x] `fetch_api()` — récupération API Opquast
  - [x] `scrape_rule(slug)` — scraping solution + controle (BeautifulSoup)
  - [x] Tests unitaires avec mocks
  - [x] Logging centralisé (`app/logging_config.py`)
  - [x] Gestion erreurs (exceptions levées si données manquantes)
  - Tests passants ✅

- [x] **Étape 2 — Agrégation**
  - [x] `app/ingestion/agregation.py`
  - [x] Classe `RuleAggregation` (Pydantic) : validation stricte
  - [x] Alias `Rule = RuleAggregation`
  - [x] Classe `Rules` (collection non-vide)
  - [x] Fonction `aggregate_rules()` : dicts → Rules validée
  - [x] Fail-fast + logging erreurs + synthèse succès
  - [x] Tests unitaires (13 tests)
  - Tests passants ✅

- [ ] **Étape 3 — Enrichissement**
  - [ ] `app/ingestion/enrichissement.py`
  - [ ] Appel LLM Kimi K2.6 (Azure)
  - [ ] Génération `strategie_analyse`, `strategie_justification`, `guide_analyse`
  - [ ] Retry logic (3 tentatives, backoff croissant)
  - [ ] Tests unitaires avec mocks

- [ ] **Étape 4 — Stockage**
  - [ ] `app/ingestion/stockage.py`
  - [ ] Upsert PostgreSQL via `numero` (idempotence)
  - [ ] Tables de référence (`theme`, `objectif`, `phase`, `tag`)
  - [ ] Tests d'intégration BDD

- [ ] **Étape 5 — Chunking**
  - [ ] `app/ingestion/chunking.py`
  - [ ] Construction texte chunk (intitulé + solution + controle + guide_analyse + tags + phases)
  - [ ] 1 chunk = 1 règle
  - [ ] Tests unitaires

- [ ] **Étape 6 — Embedding**
  - [ ] `app/ingestion/embedding.py`
  - [ ] Vectorisation via All MiniLM L12 v2 (Infomaniak)
  - [ ] Batch processing
  - [ ] Tests unitaires avec mocks

- [ ] **Étape 7 — Indexation**
  - [ ] Intégré dans `app/ingestion/stockage.py`
  - [ ] Écriture colonne `embedding`
  - [ ] Index HNSW (créé par migration BDD)

- [ ] **Orchestration**
  - [ ] `scripts/ingestion.py`
  - [ ] Chaîne les 7 étapes en séquence
  - [ ] Fail-fast + logs structurés
  - [ ] Code de sortie approprié

## Notes

- **Dépendances résolues :** `beautifulsoup4` ajoutée à `pyproject.toml`
- **Logging :** centralisé dans `app/logging_config.py`, fichier uniquement (pas console)
- **Tests :** structure `tests/unit/ingestion/`, `tests/integration/ingestion/`
- **Config :** variables `.env` en place (Opquast, LLM, BDD)
