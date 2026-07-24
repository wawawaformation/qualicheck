# Changelog

Historique des réalisations sur QualiCheck. Mis à jour par tout outil agentique utilisé (Claude Code, OpenCode...) — voir `CLAUDE.md` pour la règle d'usage.

Format d'entrée, une ligne par réalisation :

```
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

## 2026-07-23 — Claude Code

- **`docs/jury/veille/CLAUDE.md` créé** — orientation rapide pour la prochaine session sur le dossier veille : thème large (pas de vérification par veille), convention de dossier `fonds/`, format ODP/MD à deux rôles, pièges déjà rencontrés (duplication, gitlink imbriqué, `git add -A` qui re-suit un dossier exclu) — voir `docs/jury/veille/CLAUDE.md`

## 2026-07-21 — Claude Code (Part 9)

- **Dossier `docs/jury/`** — méta-documentation pour la certification — voir `docs/jury/`
  - `README.md` : index compétences C1-C21 → preuves, avec état honnête (✅/🟡/⬜) et mention explicite de ce qui manque par ligne. Deux règles posées : on pointe vers les preuves sans les recopier, et on n'écrit ici que ce qui n'a aucun autre domicile
  - `veille/` (`sources.md`, `journal.md`) : format posé, **aucune entrée inventée**. C6 exige une régularité (min. 1h/semaine) — seule exigence du référentiel impossible à produire rétroactivement
  - `decisions/` : un fichier par décision, avec options écartées. Format en clair (pas d'étiquette « ADR »). Le `README.md` indexe les décisions **antérieures** vers les documents qui les justifient déjà (`conception.md`, `bdd.md`, `1_prompt_engineering.md`...) plutôt que de les réécrire — une reconstruction tardive serait moins fidèle que l'original
  - Deux décisions documentées : périmètre MLOps de l'ingestion (7 options envisagées, 6 écartées) et choix du modèle d'enrichissement

- **`TODO.md` créé à la racine** — point d'entrée transverse (spec E, décisions en attente, veille C6, livrables de certification manquants). Ne duplique pas `TODO_PIPELINE_INGESTION.md`, qui reste la référence du pipeline

- **`conception/annexes/F_choix_llm.md` récupéré** — benchmark Azure AI Foundry (16 820 appels), argumentation C7, référencé deux fois par `conception.md` mais absent du dépôt (il était à la corbeille). Ses renvois vers `annexes/F1`-`F4` ne correspondent pas encore à l'arborescence réelle (`annexes/benchmark/`)

- **Dérive de spec détectée et corrigée dans `conception/conception.md`** — voir `conception/conception.md`, `docs/jury/decisions/2026-07-21-modele-enrichissement-latence.md`
  - Le tableau de stack annonçait `gpt-5.4-nano` pour l'enrichissement alors que le code, le `.env.example` et le `CLAUDE.md` utilisent **Kimi K2.6** — avec en plus une ligne dupliquée à l'identique, et l'exemple de configuration `ENRICHMENT_LLM = "gpt54_nano"` resté en place
  - **Origine du changement, jamais écrite jusqu'ici** : gpt-5.4-nano avait été retenu pour sa faible latence, critère sans objet sur un traitement par lot sans utilisateur en attente. Kimi K2.6 l'emporte sur la fenêtre de contexte (256K, utile à la ré-ingestion post-MVP) et la fiabilité du JSON
  - **Détectée en construisant l'index compétences → preuves** : vérifier qu'une preuve existe réellement plutôt que la supposer a fait apparaître la contradiction. C'est le *spec drift* identifié comme risque principal dans `CLAUDE.md`, confirmé en conditions réelles sur un document central
  - Constaté au passage : `conception.md` renvoie deux fois à `annexes/F_choix_llm.md`, absent du dépôt. Le matériau du benchmark existe (`annexes/benchmark/`), sa synthèse rédigée non — contenu exploitable pour C7 actuellement invisible dans le Git

## 2026-07-21 — Claude Code (Part 8)

- **Spec « Provenance des données et manifeste d'ingestion »** (conception seule, aucune implémentation) — voir `conception/2_ingestion/E_provenance_manifeste.md`
  - **Problème identifié** : une ligne de `regle` ne sait pas d'où elle vient. Aucun horodatage sur la table ; version de prompt absente de la donnée *et* du fichier `enrich_rule.md` (seulement en prose dans `1_prompt_engineering.md`) ; `llm_provider` est une chaîne en dur (`llm_client.py:129-130`, dupliquée en défaut Pydantic `schema.py:62-63`) — donc une valeur **affirmée par le code**, pas observée : elle continuerait d'annoncer `kimi-k2.6` après un changement de déploiement dans `.env`
  - **Principe directeur retenu** : une seule autorité par valeur (le code lit, ne recopie pas) et une seule responsabilité par couche — `.env` = annuaire + secrets, `manifest.yml` = décisions courantes, git = historique des décisions, colonnes de provenance = quelle décision a produit quelle ligne. Corollaire : le manifeste ne conserve **aucun** historique interne (ce serait réimplémenter git en moins bien)
  - **Décisions** : `.env` restructuré en inventaire par modèle (`AZURE_MODEL_KIMI`) et non plus par rôle ; `app/ingestion/manifest.yml` porte l'affectation rôle → modèle avec résolution explicite (`env_var:`) ; version du prompt en frontmatter de `enrich_rule.md`, format entier simple ; 4 colonnes de provenance nullables sur `regle` (`NULL` = produit avant instrumentation, donc signal de bug après le chantier 3) ; `llm_provider` **renommée** `llm_model` (elle contenait déjà un modèle sous un nom de fournisseur) ; table `ingestion_run` écartée (coût/durée déjà en prose, script lancé de façon anecdotique)
  - **Règle de nommage des colonnes formalisée** : métier en français, technique en anglais (*langage omniprésent* du DDD — le domaine Opquast **est** francophone). Le schéma l'appliquait déjà sans l'avoir écrite (`embedding`, `llm_provider` en anglais parmi des colonnes françaises). Explique pourquoi `audit.date_creation` et `regle.created_at` coexistent sans incohérence
  - **Limite assumée et documentée** : `kimi-k2.6` reste une **déclaration**, pas une observation — un déploiement Azure peut être repointé depuis la console sans qu'aucun fichier versionné ne change. À vérifier à l'implémentation si la réponse de l'API expose le modèle réellement utilisé
  - **Reste ouvert** : sort des `KIMI_PRICE_*` (relevés de tarifs Azure réels en cours de collecte)
  - Se place **entre le chantier 1 (fait) et le chantier 2 (prompt V4)**, et doit être livrée avant le chantier 3 (ré-ingestion réelle) — sinon la provenance nécessite une migration *et* une seconde ré-ingestion facturée

## 2026-07-19 — Claude Code (Part 7)

- **Chantier 1 — Correction du scraping + champ `contexte`** — voir `conception/2_ingestion/D_chantier1_scraping_contexte.md`, `app/ingestion/acquisition.py`, `app/ingestion/schema.py`, `app/ingestion/llm_client.py`, `app/ingestion/prompts/enrich_rule.md`, `app/ingestion/stockage.py`, `app/models/referentiel.py`, `app/migration/versions/0006-0007`
  - Spec validée (méthodo spec-driven, brainstorming + implementation plan via subagent-driven-development), exécutée tâche par tâche avec revue systématique
  - **`scrape_rule()` réécrite** : extraction bornée à `div.c-rule-content` (le pied de page Opquast en est structurellement exclu → plus besoin de sentinelle mot-clé), ciblage par classes émoji stables (`c-emoji-tools`, `c-emoji-check`). Corrige les 2 bugs identifiés en Part 6 (footer parasite, `<ul>` ignoré)
  - **2 variantes de structure supplémentaires découvertes en scrapant les 245 vraies règles** (non couvertes par les tests mockés initiaux) : contenu en nœud texte direct sans `<p>` (règle 14), contenu enveloppé dans `<div>` plutôt que `<p>` (règle 27). `extract_content_after()` généralisée pour traiter tout frère non-`<ul>`/`<h2>` comme un bloc de texte via `get_text()`
  - **Nouveau champ `contexte`** (texte explicatif, `c-rule-hero__subtitle`) : traverse tout le pipeline — scraping → schémas Pydantic (`RuleAcquisition`, `RuleAggregation`, hérité par `EnrichedRule`) → prompt d'enrichissement LLM (`{contexte}`, fallback `"(non disponible)"` si absent) → colonne BDD (`TEXT NULL`, migration 0006) → stockage (`upsert_rule`, `load_enriched_rules_from_db`)
  - **Recalibrage `solution`/`controle`** (migration 0007) : `VARCHAR(1024)` → `VARCHAR(2048)`. Le scraping corrigé capture désormais le contenu complet (non tronqué) ; les vraies données dépassent l'ancienne limite calibrée sur des données elles-mêmes tronquées par les bugs (max observé sur 245 règles réelles : solution 1880, controle 1156)
  - **Validation pré-LLM** : dump JSON des 245 règles acquises dans `tmp/rules_acquises.json` (scraping + stockage réels, enrichissement bouchonné) — scraping et stockage complets validés sans coût LLM avant de poursuivre vers la ré-ingestion réelle
  - **Revue finale whole-branch** (10 commits) : aucun Critical/Important, 2 findings mineurs corrigés (incohérence des numéros de règles cités en exemple dans une docstring ; `solution`/`controle` passés de `VARCHAR(2048)` à `TEXT`, migration 0008, pour aligner sur `contexte` et éviter un 3e recalibrage si Opquast allonge son contenu — Postgres stocke `TEXT`/`VARCHAR(n)` de façon identique, la limite n'apportait aucun gain)

## 2026-07-19 — Claude Code (Part 6)

- **Ingestion complète des 245 règles + analyse de la classification LLM** — voir `docs/problemes_rencontres/recommandations_v4.md`, `scripts/ingestion.py`, `app/ingestion/stockage.py`, `docs/schemas/ingestion_activite.drawio`, `conception/2_ingestion/C_pipeline_ingestion.drawio`
  - Ingestion réelle des 245 règles Opquast menée à terme (enrichissement Kimi K2.6, prompt V3) : ~1,2 M tokens, coût ~3 €. Distribution `strategie_analyse` : statique 46 %, playwright 42 %, vision 8 %, manuel 4 %
  - **Hook `--resume`** ajouté à `scripts/ingestion.py` + `load_enriched_rules_from_db()` dans `app/ingestion/stockage.py` : permet de reprendre le pipeline depuis les règles déjà enrichies en BDD (saute étapes 1-4, évite de refaire les appels LLM coûteux) — schémas d'activité mis à jour en conséquence
  - **Revue manuelle règle par règle** de la classification (démarche buffer `ob_start`/`ob_get_clean`) → document `docs/problemes_rencontres/recommandations_v4.md` (feuille de recommandations priorisées pour la V4)
  - **2 bugs de scraping critiques identifiés** (`scrape_rule()`) affectant > 60 règles (> 25 %) : (1) footer légal Opquast capturé à la place de solution/controle sur 43 règles ; (2) contenu en `<ul>` ignoré (seul le `<p>` d'intro pris) sur ~34 règles. Cause commune : `find_next("p")` non borné. Solution identifiée : cibler `<div class="c-rule-content">` + classes `c-emoji-tools`/`c-emoji-check` + capturer p+ul. Correction et ré-ingestion à venir
  - Pistes prompt V4 : stratégies composites (`vision+statique`, `playwright+vision`), critère « observation hors page web = manuel », factuel > spéculatif, acquisition du texte explicatif (`c-rule-hero__subtitle`) pour améliorer le contexte LLM
  - Déplacement `conception/3_enrichissement/prompt_engineering.md` → `docs/problemes_rencontres/prompt_engineering.md` (regroupement des docs de problèmes rencontrés)
  - `.gitignore` : ajout de `tmp/` (matériel de travail) et `.*.drawio.dtmp` (fichiers temporaires draw.io)

## 2026-07-19 — Claude Code (Part 5)

- **Schéma BDD — Calibrage des colonnes textuelles (VARCHAR vs TEXT)** — voir `app/models/referentiel.py`, `app/migration/versions/0002-0005`, `scripts/ingestion_test.py`, `docs/problemes_rencontres/schema_text_columns.md`
  - **Problème identifié** : première ingestion complète échoue à règle 154 → `objectif` dépasse `VARCHAR(256)`, puis à règle 166 → `solution` dépasse `VARCHAR(512)`
  - **Root cause** : colonnes `solution` et `controle` scrappées depuis le site Opquast (contenu HTML brut) peuvent dépasser les limites estimées ; `objectif` vient de l'API mais bien plus long que prévu
  - **Stratégie** : conversion temporaire en `TEXT` (migrations 0002-0004), puis script de test `ingestion_test.py` (bouchons LLM, pas d'appels coûteux) peuple la BD avec 245 règles réelles et révèle les max
  - **Mesure des données réelles** : `intitule` MAX 167 / `solution` MAX 569 / `controle` MAX 573 / `objectif` MAX 359
  - **Recalibrage final** (migration 0005) :
    - `intitule` : `VARCHAR(255)` (marge 88 chars)
    - `solution` : `VARCHAR(1024)` (marge 455 chars)
    - `controle` : `VARCHAR(1024)` (marge 451 chars)
    - `objectif` : `VARCHAR(512)` (marge 153 chars)
    - `strategie_analyse`, `strategie_source` : `VARCHAR(32)` (énumérées, court)
    - Conservé en `TEXT` : `strategie_justification`, `guide_analyse` (enrichissement LLM, imprévisible)
  - **Validation** : 245 règles stockées sans erreur avec le schéma final
  - **Documentation** : document `schema_text_columns.md` trace la démarche (observation → hypothèse → test → mesure → décision) pour valeur pédagogique auprès du jury
  - **Économie** : script de test évite ~240 appels LLM supplémentaires (coûteux en tokens)

## 2026-07-19 — Claude Code (Part 4)

- **Correctif — Restauration de `theme` + `tags` optionnels (pipeline d'ingestion)** — voir `app/ingestion/schema.py`, `app/ingestion/acquisition.py`, `app/migration/versions/0001_schema_initial.py`, `app/models/referentiel.py`, `app/ingestion/stockage.py`, `app/ingestion/llm_client.py`, et fichiers de tests associés
  - Corrige la suppression erronée de `theme`/`theme_id` faite en Part 3 (le MCD prévoyait bien une relation 1-N via `regle.theme_id`, pas une relation many-to-many comme supposé à tort) — confirmé par les données réelles de l'API Opquast : les 245 règles ont chacune exactement une valeur `Thématiques`
  - Table `theme` + FK `regle.theme_id` (NOT NULL) restaurées dans la migration 0001 et dans `app/models/referentiel.py`
  - `RuleAcquisition`/`RuleAggregation` (Pydantic) : ajout du champ `theme: str` (non-vide), mappé depuis `metadata.Thématiques[0]` en acquisition
  - `tags` rendu optionnel (liste vide acceptée) côté validation Pydantic — confirmé par les données réelles : 64 des 245 règles Opquast n'ont aucun tag
  - `upsert_rule()` (stockage) résout `theme` via `get_or_create()` et assigne `regle.theme_id` directement (FK scalaire, pas de table d'association)
  - Tests unitaires mis à jour (fixtures acquisition/aggregation/enrichment avec `theme=...`) + nouveaux tests (tags vides acceptés, validation theme) ; tests de migration mis à jour (14 tables attendues)
  - Correctif production dans `llm_client.py` : `enrich_single_rule()` ne passait pas `theme` à `EnrichedRule` — aurait levé une `ValidationError` en production, découvert en mettant à jour les tests d'enrichissement
  - Vérification finale : 25 tests unitaires + 10 tests migration, tous verts ; `ruff check` clean sur `app/`, `tests/`, `scripts/`

## 2026-07-19 — Claude Code (Part 3)

- **Étape 4 — Stockage (pipeline d'ingestion)** — voir `app/ingestion/stockage.py`, `scripts/ingestion.py`
  - `get_or_create()` : fonction générique idempotente pour Objectif/Phase/Tag
  - `upsert_rule()` : upsert Regle via numero (UPDATE complet si présent, INSERT sinon), synchronise les associations many-to-many (delete + recrée)
  - `store_rules()` : orchestration de toute la collection EnrichedRules dans une transaction unique, fail-fast avec rollback complet
  - `embedding` reste NULL à cette étape (écrit plus tard, Étape 7)
  - `scripts/ingestion.py` : première version, orchestre Étapes 1-4, fail-fast avec log explicite par étape et code de sortie non-nul
  - Pas de suite pytest pour cette étape — validation par exécution réelle du script (3 règles Opquast réelles, appels LLM réels) + inspection directe des tables PostgreSQL, y compris test d'idempotence (ré-exécution → pas de doublons)
  - Correctif préalable : suppression de `theme`/`theme_id` du MCD (erreur de conception, relation déjà couverte par `tag`) — migration 0001 corrigée directement (jamais mergée dans `main`)
  - Bug corrigé en cours de validation : `LLMClient` utilisait `AzureChatOpenAI` (exige `api_version`, format d'URL Azure classique incompatible avec l'endpoint `/openai/v1` unifié) — remplacé par `ChatOpenAI` (client OpenAI standard, conforme à l'exemple du portail Azure AI Foundry)

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
