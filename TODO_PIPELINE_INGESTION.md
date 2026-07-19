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
  - [x] `app/ingestion/aggregation.py`
  - [x] Classe `RuleAggregation` (Pydantic) : validation stricte
  - [x] Alias `Rule = RuleAggregation`
  - [x] Classe `Rules` (collection non-vide)
  - [x] Fonction `aggregate_rules()` : dicts → Rules validée
  - [x] Fail-fast + logging erreurs + synthèse succès
  - [x] Tests unitaires (13 tests)
  - Tests passants ✅

- [x] **Étape 3 — Enrichissement**
  - [x] `app/ingestion/enrichment.py`
  - [x] Classe `EnrichedRule` (Pydantic) : extension RuleAggregation
  - [x] Classe `EnrichedRules` (collection non-vide)
  - [x] Fonction `enrich_rules()` : Rules → EnrichedRules
  - [x] `LLMClient` avec LangChain (langchain_core) + Azure Kimi K2.6
  - [x] Retry logic (3 tentatives, backoff 2s/4s via tenacity)
  - [x] Logging : erreur critique, synthèse succès
  - [x] Few-shot prompt dans `prompts/enrich_rule.md`
  - [x] Tests unitaires (6 tests)
  - Tests passants ✅

- [x] **Étape 4 — Stockage**
  - [x] `app/ingestion/stockage.py`
  - [x] `get_or_create()` : générique, idempotent (Objectif/Phase/Tag)
  - [x] `upsert_rule()` : upsert via numero, sync associations
  - [x] `store_rules()` : transaction globale, fail-fast, logging
  - [x] `scripts/ingestion.py` : orchestrateur partiel (Étapes 1-4)
  - Validation par exécution réelle (3 règles, LLM réel) + inspection BDD + test d'idempotence — pas de suite pytest ✅

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

- [ ] **Orchestration** (partiellement fait, voir Étape 4)
  - [x] `scripts/ingestion.py` créé, chaîne les Étapes 1-4
  - [ ] Étendre aux Étapes 5-7 (chunking, embedding, indexation)
  - [x] Fail-fast + logs structurés (Étapes 1-4)
  - [x] Code de sortie approprié (Étapes 1-4)

## Notes

- **Dépendances résolues :** `beautifulsoup4` ajoutée à `pyproject.toml`
- **Logging :** centralisé dans `app/logging_config.py`, fichier uniquement (pas console)
- **Tests :** structure `tests/unit/ingestion/`, `tests/integration/ingestion/`
- **Config :** variables `.env` en place (Opquast, LLM, BDD)
