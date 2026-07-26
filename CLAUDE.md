# QualiCheck

Application web d'aide à l'audit qualité web, basée sur le référentiel Opquast (245 règles). Agents LLM + pipeline RAG (pgvector) + feedback loop.

> Ce fichier ne répète pas les règles générales déjà posées dans `~/.claude/CLAUDE.md` (philosophie, conventions de code, pédagogie). Il ne couvre que ce qui est spécifique à QualiCheck.

## Contexte du projet

QualiCheck est le **projet de certification** présenté devant un jury pour valider une formation développeur IA agentique — **courte**. L'utilisateur est développeur PHP confirmé, à l'aise en ligne de commande/Linux, mais **pas Python, pas agentique, pas LLM à la base** : ce sont les compétences que la formation (et ce projet) doivent démontrer.

Conséquence directe sur la façon de travailler : **comprendre chaque ligne générée n'est pas optionnel**. Ce n'est pas un projet perso où "ça marche" suffit — c'est un projet où l'utilisateur doit pouvoir expliquer et défendre chaque choix devant un jury. D'où la validation à chaque étape et la pédagogie ciblée ci-dessous : elles découlent directement de cet enjeu, pas d'une préférence de confort.

**Périmètre de couverture** : l'objectif est que QualiCheck couvre l'intégralité des 3 blocs de compétences (C1-C21). À ce stade (2/3 de la formation restant), la visibilité est encore incomplète sur certains blocs — si une compétence s'avère trop artificielle à rattacher à QualiCheck, un brief distinct et ponctuel pourra être traité séparément pour cette compétence précise, plutôt que de forcer un rattachement mal justifié.

## Changelog

L'utilisateur alterne entre plusieurs outils agentiques (Claude Code, OpenCode...) qui ne partagent pas de mémoire entre eux. Un fichier `CHANGELOG.md` à la racine du projet est donc la seule continuité fiable : **chaque réalisation (fichier créé, migration appliquée, script modifié...) doit y être déclarée**, quel que soit l'outil utilisé.

Format d'entrée, une ligne par réalisation :

```text
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

Avant de commencer une tâche d'implémentation, lire `CHANGELOG.md` pour savoir où en est le projet, en complément (pas en remplacement) des documents de `conception/`.

## Makefile

Point d'entrée pour les commandes courantes — s'enrichit au fur et à mesure du projet, pas figé. Cibles actuelles :

| Cible | Rôle |
| --- | --- |
| `make up` | Démarre les conteneurs Docker (build si nécessaire) |
| `make down` | Éteint les conteneurs |
| `make migration` | Applique les migrations Alembic (crée le schéma BDD) |
| `make downgrade` | Annule les migrations (`alembic downgrade base`) — permet de retester une migration from scratch |
| `make migration-test` | Crée (si absente) et migre la base de test dédiée `qualicheck_test` (`POSTGRES_TEST_DB`), utilisée par les tests d'intégration destructeurs |
| `make ingestion` | Lance l'ingestion des règles Opquast, puis `make export_sql` automatiquement — `LIMIT=n` pour ne traiter que les n premières règles (ex : `make ingestion LIMIT=5`) |
| `make clear` | Vide les tables Opquast de la base de données (utile pour retester une ingestion) |
| `make export_sql` | Exporte les données réelles (`pg_dump --data-only`, hors `alembic_version`) dans `backups/YYYYMMDD_HHMMSS.sql` (dossier gitignoré) — à lancer avant toute ré-ingestion réelle coûteuse |
| `make import_sql FILE=...` | Restaure un dump `export_sql` dans la base réelle — `FILE=` obligatoire ; échoue explicitement en cas de conflit de clé primaire (ne vide rien tout seul, voir `make clear` si besoin) |
| `make enrich-again` | Rappelle le LLM sur les règles `review_status = a_revoir`/`invalide` (tient compte de `review_note`), vide ces champs après correction — `make export_sql` avant (backup pré-run) et après |
| `make embed-rules` | Recalcule l'embedding de toutes les règles (`text-embedding-3-small`, `dimensions=1536`), puis `make export_sql` |
| `make test` | Lance toute la suite (`pytest tests/`) — nécessite les conteneurs démarrés, les migrations appliquées, et `make migration-test` pour les tests d'intégration destructeurs |
| `make test-unit` | Lance uniquement `tests/unit` — aucune BDD requise |
| `make test-integration` | Lance uniquement `tests/integration` — nécessite `make migration-test` pour les tests destructeurs |
| `make test-migration` | Lance uniquement `tests/migration` — nécessite les migrations appliquées |
| `make psql` | Ouvre une session `psql` interactive dans le conteneur Postgres |

À jour ici pour référence rapide, mais le `Makefile` lui-même reste la source de vérité — le relire directement en cas de doute plutôt que de se fier uniquement à ce tableau.

## CI (GitHub Actions)

`.github/workflows/ci-feature.yml` — déclenché sur push sur toute branche sauf `main`/`dev`/`staging` (branches de travail type `feature`). Étapes : `uv sync` → `ruff check` → `scripts/migration.py` (contre un service `pgvector/pgvector:pg17` éphémère, pour vérifier que les migrations s'appliquent) → `pytest tests/unit tests/integration`.

- **Secrets BDD** (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) gérés via **GitHub Secrets**, pas via `.env` — le `.env` reste strictement local, jamais commité ; les secrets CI sont une configuration séparée côté GitHub. `POSTGRES_TEST_DB` du workflow réutilise volontairement la valeur du secret `POSTGRES_DB` (aucun secret dédié créé) — la base du service CI étant déjà éphémère à chaque run, cette réutilisation ne recrée pas le risque de l'incident du 2026-07-25.
- Le CI n'exécute **pas** `scripts/ingestion.py` (évite de vrais appels LLM facturés à chaque push) — les tests couvrent le code applicatif (unitaire + intégration), pas le pipeline d'ingestion réel.
- `tests/migration/` (et un futur `tests/acceptance/`) sont volontairement exclus de ce workflow — scope de tests plus léger pour une branche de travail. Réservés à un futur workflow dédié `dev`/`staging` (pas encore écrit, ces branches n'existent pas encore) avec une suite plus complète avant promotion.

## Stack

- Backend : FastAPI (Python)
- Frontend : Vue.js
- BDD : PostgreSQL + pgvector (index HNSW, `vector(384)`)
- Migrations : Alembic
- Gestion de paquets/environnement : `uv`
- Linter : Ruff
- LLM (dev) : Kimi K2.6 (enrichissement ingestion), gpt-5.4 / gpt-5.4-mini (audit, question libre) via Azure
- Embedding : Azure `text-embedding-3-small` (`dimensions=384`), solution actuelle — cible visée à terme : BGE Multilingual Gemma2 via Infomaniak (gratuit, encore `coming_soon` au 2026-07-26). MiniLM L12 v2 (initialement visé) disqualifié : `max_token_input=128`, incompatible avec le choix "1 règle = 1 chunk" (~319 tokens en moyenne, jusqu'à ~952)
- Déploiement : Docker + docker-compose

## `.env`

Un seul fichier, à la racine, jamais versionné : connexion BDD + accès LLM (endpoint Azure, clés, noms de déploiements).

## Ordre d'exécution du projet

1. `scripts/migration.py` — crée le schéma BDD complet (vide). Voir `conception/1_BDD/bdd.md`.
2. `scripts/ingestion.py` — peuple le référentiel Opquast (245 règles). Voir `conception/2_ingestion/ingestion.md`.
3. Reste de l'application (audits, dialogue, question libre) — non conçu à ce stade.

## Structure du repo

```text
.github/workflows/ci-feature.yml   # lint + migrations + tests unit/intégration sur push (hors main/dev/staging)
conception/          # documents de conception, non exécutés — source de vérité fonctionnelle
  conception.md       # dossier de conception complet (US0/US1/US2, flux, MCD, choix techniques...) — document central
  1_BDD/bdd.md
  2_ingestion/ingestion.md
  MLD_qualicheck.md
  A_dictionnaire_donnees_qualicheck.xlsx
  B_MCD_qualicheck.drawio
  referentiel_competences.md   # référentiel de certification (C1-C21) — à consulter au moment de rédiger un livrable
  certif_deroule.md             # déroulé, épreuves (E1-E5), critères pratiques de la certification
scripts/             # points d'entrée uniquement, à plat — voir scripts/CLAUDE.md
  migration.py
  ingestion.py
app/                  # domaine métier + modules de support — voir app/CLAUDE.md
  models/
  migration/
  ingestion/
logs/                # logs d'exécution des scripts (une ligne par règle × étape pour l'ingestion) — distinct du CHANGELOG.md
tests/               # tests exécutés par le CI (pytest)
docker-compose.yml
.env
CHANGELOG.md         # historique des réalisations (implémentation), mis à jour par tout outil agentique utilisé
IDEA.md               # idées en vrac, non actées — à distinguer de TODO.md (décidé) et conception/ (validé)
Makefile             # commandes courantes (up, down, migration, downgrade, test...) — voir section dédiée
```

## Méthodologie : spec-driven, par incrément

Chaque brique du projet suit un cycle **spec → validation → implémentation**, jamais l'inverse : pas de code écrit sans document de conception validé au préalable dans `conception/` pour le périmètre concerné. Chaque document de conception (`bdd.md`, `ingestion.md`, les suivants à venir) est une spec complète pour *sa* brique, pas pour l'application entière — la vision globale se précise brique par brique, pas d'un coup.

Le risque à surveiller : le **spec drift** (le code qui s'éloigne de la spec au fil des sessions, en particulier en alternant Claude Code et OpenCode). D'où l'importance de toujours relire la spec correspondante avant de modifier du code existant, et de tenir `CHANGELOG.md` à jour — c'est ce qui maintient le lien entre "ce qui a été décidé" et "ce qui existe réellement".

## Stratégie de branches

Une branche par sujet plutôt qu'un `feature` fourre-tout : `veille` (déjà créée,
2026-07-23), `feature-ingestion`, `conception`, etc. — noms indicatifs, pas figés,
à créer **au fil de l'eau** quand un nouveau sujet démarre, pas par anticipation.

La branche `feature` existante (mélange ingestion + conception + veille avant ce
découpage) **n'est pas splittée rétroactivement** — reconstituer l'historique par
sujet coûterait plus cher (rebase/cherry-pick sur de l'historique déjà poussé)
que la valeur obtenue. Le découpage par sujet s'applique au travail à venir, pas
à l'existant.

## Mode de travail sur ce projet

*(découle directement du contexte de certification ci-dessus)*

- **Validation à chaque étape** : contrairement au défaut plus autonome de `~/.claude/CLAUDE.md`, sur QualiCheck on s'arrête et on fait valider chaque étape avant de continuer — même quand ce n'est pas strictement bloquant. Priorité sur le défaut général pour ce projet.
- **Pédagogie ciblée** : expliciter le raisonnement sur les outils/concepts découverts via ce projet (Alembic, pgvector/HNSW, RAG, `uv`, agents LLM...) — pas seulement sur ce qui relève de PHP/ligne de commande, déjà maîtrisés.

## Principes généraux (tout le projet)

- **Retry LLM** : 3 tentatives avec backoff croissant sur tout appel LLM, avant de considérer l'appel en échec définitif.
- **Tests d'intégration Postgres destructeurs** : tout test qui écrit/vide des données réelles (`clear_opquast_tables()`, insertions, etc.) doit utiliser `POSTGRES_TEST_DB` (base dédiée `qualicheck_test`, provisionnée via `make migration-test`), jamais `POSTGRES_DB` directement. Suite à l'incident du 2026-07-25 : un `pytest tests/` lancé juste après une ré-ingestion réelle (245 règles, 4,32 €) a effacé ces données via un test d'intégration qui vidait la vraie base de dev locale. Ne s'applique pas aux tests en lecture seule sur le schéma (`tests/migration/`) — leur but est justement de vérifier la vraie base de dev, `POSTGRES_DB` y reste volontaire. En CI, `POSTGRES_TEST_DB` réutilise délibérément le secret `POSTGRES_DB` (la base du service CI est déjà éphémère à chaque run) — ne pas reproduire cette égalité en local, ça recréerait l'incident.

## Documents de référence à consulter avant toute implémentation

- `conception/conception.md` — document central : US0/US1/US2, flux fonctionnels, MCD, choix techniques, personas, RGPD, budget
- `conception/1_BDD/bdd.md` — création et gestion du schéma (Alembic, pgvector, HNSW)
- `conception/2_ingestion/ingestion.md` — pipeline d'ingestion en détail (7 étapes)
- `conception/MLD_qualicheck.md` — modèle logique de données, source de vérité pour les champs/contraintes
- `conception/A_dictionnaire_donnees_qualicheck.xlsx` — dictionnaire de données détaillé

## Documents de référence pour la certification (à consulter au moment de rédiger un livrable, pas pour le code courant)

- `conception/referentiel_competences.md` — référentiel détaillé C1-C21 : ce que chaque compétence exige concrètement (versionnement Git, documentation accessible, tests, etc.)
- `conception/certif_deroule.md` — déroulé de la certification, épreuves E1-E5, critères pratiques (nombre de pages, timing...)
