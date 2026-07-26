# Pipeline d'Ingestion — État d'avancement

Référence : `conception/2_ingestion/ingestion.md`

## Étapes du pipeline

- [x] **Étape 1 — Acquisition** — scraping corrigé (chantier 1, voir `conception/2_ingestion/D_chantier1_scraping_contexte.md`)
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
  - [ ] **Décision 2026-07-26** : vectorisation via Azure `text-embedding-3-small`
    (`dimensions=384`, déploiement Azure vérifié : `GenerallyAvailable`,
    8191 tokens de contexte, 125 000 TPM / 750 RPM, mise hors service
    02/2028) en solution actuelle — les 3 modèles d'embedding du catalogue
    Infomaniak (`mini_lm_l12_v2`, `bge_multilingual_gemma2`,
    `Qwen3-Embedding-8B`) sont encore en `coming_soon`. `dimensions=384`
    évite une migration de schéma (`regle.embedding` reste `vector(384)`),
    mais **n'évite pas** une ré-vectorisation complète du référentiel au
    moment du bascule vers Infomaniak — deux modèles différents produisent
    des espaces vectoriels non comparables, même à dimension égale
  - [ ] **`mini_lm_l12_v2` disqualifié comme cible finale** : `max_token_input=128`,
    incompatible avec la décision actée "1 règle = 1 chunk" (mesuré sur les
    245 règles réelles : ~319 tokens en moyenne, jusqu'à ~952 pour la règle
    164) — aucun chunk ne rentrerait sous cette limite. Cible Infomaniak
    revue : **BGE Multilingual Gemma2** (`max_token_input=8000`, large
    marge), à confirmer (dimension de sortie non documentée dans le
    catalogue, à vérifier quand le modèle passera en `ready`)
  - [ ] Batch processing
  - [ ] Tests unitaires avec mocks
  - [ ] **À prévoir plus tard** : script de ré-vectorisation (recalcul de
    `embedding` pour les 245 lignes) quand BGE Multilingual Gemma2 (ou un
    autre modèle Infomaniak compatible ≥ 952 tokens) passera en `ready` —
    hors périmètre tant que ce n'est pas le cas

- [ ] **Étape 7 — Indexation**
  - [ ] Intégré dans `app/ingestion/stockage.py`
  - [ ] Écriture colonne `embedding`
  - [ ] Index HNSW (créé par migration BDD)

- [ ] **Orchestration** (partiellement fait, voir Étape 4)
  - [x] `scripts/ingestion.py` créé, chaîne les Étapes 1-4
  - [x] Hook `--resume` : reprise depuis les règles enrichies en BDD (`load_enriched_rules_from_db()`), évite de refaire les appels LLM
  - [ ] Étendre aux Étapes 5-7 (chunking, embedding, indexation)
  - [x] Fail-fast + logs structurés (Étapes 1-4)
  - [x] Code de sortie approprié (Étapes 1-4)

## Ingestion réelle & analyse (2026-07-19)

- [x] **Ingestion complète des 245 règles** menée à terme (Kimi K2.6, prompt V3, ~1,2 M tokens, ~3 €)
- [x] **Revue manuelle de la classification** règle par règle → `docs/problemes_rencontres/3_recommandations_v4.md`
- [x] **Corriger le scraping** (R1.1/R1.2) — fait, chantier 1 (spec-driven, 5 tâches revues par subagent-driven-development)
- [x] **Acquérir le texte explicatif** (R1.3) — fait, champ `contexte` (BDD `TEXT`, migration 0006) branché jusqu'au prompt LLM
- [x] **Recalibrage `solution`/`controle`** (`VARCHAR(1024)` → `VARCHAR(2048)`, migration 0007) — le scraping corrigé capture du contenu plus long qu'avant (données précédentes tronquées par les bugs)
- [ ] **Prompt V4** (R2.x) : stratégies composites, critère hors-page = manuel, factuel > spéculatif, marqueur « ET », multi-pages
- [ ] **Ré-ingérer sur données saines** (R3.1) — appels LLM réels sur les 245 règles avec scraping corrigé, puis re-valider les classifications (R3.2)
- [ ] Reclassement règle 111 → `manuel`

> ⚠️ Les Étapes 5-7 (chunking, embedding, indexation) ne doivent pas être attaquées avant la ré-ingestion réelle (prompt V4 + appels LLM) : le stockage actuel contient encore les données de l'ingestion V3 pré-correction.

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
