# Pipeline d'Ingestion — État d'avancement

Référence : `conception/2_us0/ingestion/ingestion.md`

## Prochain gros morceau

- [x] **API référentiel (étage données) — implémentée (2026-07-28)** —
  `app/api_regles/` : `GET /regles` (filtres `?outil=`/`?review_status=`),
  `GET /regles/{numero}`, `PATCH /regles/{numero}` (annotation de revue),
  `/health`, documentation OpenAPI, suite d'acceptance sur données réelles
  (`make api-regles-acceptance`). 64 tests verts. Spec
  `docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`, plan
  `docs/superpowers/plans/2026-07-26-api-regles-implementation.md`, décision de
  lecture ouverte `jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`,
  séparation des services `jury/decisions/2026-07-28-separation-api-regles-api-audit.md`
- [ ] **API audit** — `app/api_audit/` pour les tables métier de l'audit
  (`Audit`/`Page`/`AuditPage`/`AuditRegle`/`Constat`/`Utilisateur`), à
  concevoir avec la spec US1
- [ ] **API applicative** — `app/api_business/` pour l'orchestration US1/US2, à
  concevoir. Elle consommera les deux API données en HTTP et ne touchera pas
  PostgreSQL

## Étapes du pipeline

- [x] **Étape 1 — Acquisition** — scraping corrigé (chantier 1, voir `conception/2_us0/ingestion/D_chantier1_scraping_contexte.md`)
  - [x] `build_rule_url(slug)` — construction URL scraping
  - [x] `fetch_api()` — récupération API Opquast
  - [x] `scrape_rule(slug)` — extraction bornée à `div.c-rule-content` + classes `c-emoji-tools`/`c-emoji-check`, capture `<p>`/`<ul>`/`<div>`/texte direct — **2 bugs initiaux corrigés (footer, `<ul>` ignoré) + 2 variantes supplémentaires découvertes sur les 245 vraies règles (nœud texte direct, contenu en `<div>`)**
  - [x] Tests unitaires avec mocks (10 tests, structure HTML réelle Opquast)
  - [x] Logging centralisé (`app/logging_config.py`)
  - [x] Gestion erreurs (fail-fast conservé, sans sentinelle mot-clé — bornage structurel suffit)
  - [x] **Ajouté (R1.3)** : acquisition du texte explicatif (`c-rule-hero__subtitle`) → champ `contexte`, traverse tout le pipeline jusqu'au prompt LLM
  - Tests passants ✅ + validation sur scraping réel des 245 règles (`tmp/rules_acquises.json`)

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
  - [x] `LLMClient` avec LangChain (langchain_core) + Azure (modèle : `app/ingestion/manifest.yml`, rôle `enrichissement`)
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

- [x] **Étape 5 — Chunking**
  - [x] `app/ingestion/chunking.py`
  - [x] Construction texte chunk (intitulé + solution + controle + guide_analyse + tags + phases)
  - [x] 1 chunk = 1 règle
  - [x] Tests unitaires (`tests/unit/ingestion/test_chunking.py`)

- [x] **Étape 6 — Embedding**
  - [x] `app/ingestion/embedding.py`
  - [x] **Décision actée** : vectorisation via Azure, 1536 dimensions
    (modèle : `app/ingestion/manifest.yml`, rôle `embedding`)
  - [x] Batch processing (`scripts/embed_rules.py`, `BATCH_SIZE = 50`)
  - [x] Tests unitaires avec mocks (`tests/unit/ingestion/test_embedding.py`)
  - [x] **Exécuté pour de vrai** (2026-07-26, `make embed-rules`) : 245/245
    règles vectorisées, 0,0016 € — voir `CHANGELOG.md`

- [x] **Étape 7 — Indexation**
  - [x] Intégré dans `app/ingestion/stockage.py`
  - [x] Écriture colonne `embedding`
  - [x] Index HNSW (créé par migration BDD) — vérifié en base (`regle_embedding_idx`)
  - [x] Tests (`tests/integration/ingestion/test_stockage_embedding.py`)

- [x] **Orchestration**
  - [x] `scripts/ingestion.py` créé, chaîne les Étapes 1-4
  - [x] Hook `--resume` : reprise depuis les règles enrichies en BDD (`load_enriched_rules_from_db()`), évite de refaire les appels LLM
  - [x] Étapes 5-7 orchestrées via `scripts/embed_rules.py` + `make embed-rules`
    (chaîne chunking → embedding → upsert, hors `ingestion.py`)
  - [x] Fail-fast + logs structurés (toutes étapes)
  - [x] Code de sortie approprié (toutes étapes)

## Ingestion réelle & analyse (2026-07-19)

- [x] **Ingestion complète des 245 règles** menée à terme (modèle du rôle
  `enrichissement` du manifest, prompt V3, ~1,2 M tokens, ~3 €)
- [x] **Revue manuelle de la classification** règle par règle → `docs/problemes_rencontres/3_recommandations_v4.md`
- [x] **Corriger le scraping** (R1.1/R1.2) — fait, chantier 1 (spec-driven, 5 tâches revues par subagent-driven-development)
- [x] **Acquérir le texte explicatif** (R1.3) — fait, champ `contexte` (BDD `TEXT`, migration 0006) branché jusqu'au prompt LLM
- [x] **Recalibrage `solution`/`controle`** (`VARCHAR(1024)` → `VARCHAR(2048)`, migration 0007) — le scraping corrigé capture du contenu plus long qu'avant (données précédentes tronquées par les bugs)
- [x] **Prompt V5 puis V6** (R2.x et au-delà) : stratégies composites, critère hors-page = manuel,
  factuel > spéculatif — prompt bumpé en `version: 6` (`app/ingestion/prompts/enrich_rule.md`),
  voir `docs/problemes_rencontres/ingestion/5_recommandations_v6.md`
- [x] **Correction ciblée des données** (`make enrich-again`, 2026-07-26) — 11 règles
  à revoir corrigées sur la base des anticipations de l'audit V6 (0,1610 €). Le
  stockage contient désormais des données propres (V5 + corrections V6 ciblées) ;
  une ré-ingestion complète sur le prompt V6 n'est pas jugée nécessaire dans
  l'immédiat, reportée à un besoin plus large — voir `TODO.md`
- [x] Reclassement règle 111 → `manuel` — déjà en base (`strategie_analyse = manuel`,
  `strategie_source = ia_import`), fait lors de l'ingestion réelle

## Notes

- **Dépendances résolues :** `beautifulsoup4` ajoutée à `pyproject.toml`
- **Logging :** centralisé dans `app/logging_config.py`, fichier uniquement (pas console)
- **Tests :** structure `tests/unit/ingestion/`, `tests/integration/ingestion/`
- **Tests d'acceptance (US0) :** reportés à dessein — décidé le 2026-07-25. Le
  critère d'acceptation d'US0 (`annexes/G_user_stories_qualicheck.png`) exige
  "vectorisées et indexées dans pgvector", donc n'est atteignable qu'une fois
  les Étapes 5-7 terminées. Écrire le test avant ferait un rouge permanent par
  construction, pas un signal de bug
- **Config :** variables `.env` en place (Opquast, LLM, BDD)
- **Légende :** `[x]` fait · `[~]` fait mais à revoir · `[ ]` à faire
