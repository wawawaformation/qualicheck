.PHONY: up up-db up-staging down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again embed-rules rag-acceptance rag-dense-acceptance mesure-scores-refus mesure-variantes-chunks mesure-combinaisons-chunks mesure-multi-vecteurs-chunks mesure-guardrail-perimetre api-regles api-regles-acceptance api-regles-dense-acceptance regles-api-client-install regles-api-client regles-api-client-test

# ============================================================
# Docker
# ============================================================

## Démarre tous les conteneurs Docker (construit les images si nécessaire)
up:
	docker compose up -d --build

## Démarre uniquement Postgres — préalable aux migrations sur un environnement
## neuf où le reste de la stack n'a jamais tourné (ex. premier déploiement staging)
up-db:
	docker compose up -d postgres

## Démarre les conteneurs sans reconstruire — utilise l'image déjà tirée du
## registre (CD staging uniquement, jamais en développement local)
up-staging:
	docker compose up -d

## Éteint tous les conteneurs Docker
down:
	docker compose down

# ============================================================
# Migrations (Alembic)
# ============================================================

## Crée la base du domaine audit si elle est absente (idempotent)
create-db-audit:
	uv run python scripts/create_db_audit.py

## Applique les migrations Alembic (crée le schéma BDD)
migration:
	uv run python scripts/migration.py

## Supprime toutes les tables (downgrade Alembic) — permet de retester une migration from scratch
downgrade:
	cd app/migration && uv run alembic downgrade base

## Crée (si absente) et migre la base de test dédiée aux tests d'intégration
## destructeurs (jamais la base de dev réelle)
migration-test:
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d postgres -tc \
		"SELECT 1 FROM pg_database WHERE datname = '$$(grep '^POSTGRES_TEST_DB=' .env | cut -d= -f2)'" | grep -q 1 || \
		docker exec qualicheck-postgres createdb -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" "$$(grep '^POSTGRES_TEST_DB=' .env | cut -d= -f2)"
	POSTGRES_DB="$$(grep '^POSTGRES_TEST_DB=' .env | cut -d= -f2)" uv run python scripts/migration.py

## Migre la base du domaine audit (la crée si absente)
migration-audit: create-db-audit
	uv run python scripts/migration.py audit

## Crée (si absente) et migre la base de test du domaine audit
migration-audit-test:
	POSTGRES_DB_AUDIT="$$(grep POSTGRES_TEST_DB_AUDIT .env | cut -d= -f2)" \
		uv run python scripts/create_db_audit.py
	POSTGRES_DB_AUDIT="$$(grep POSTGRES_TEST_DB_AUDIT .env | cut -d= -f2)" \
		uv run python scripts/migration.py audit

# ============================================================
# Ingestion et données réelles
# ============================================================

## Lance le script d'ingestion des règles Opquast dans la base de données,
## puis sauvegarde les données réelles (make export_sql)
## LIMIT=n pour ne traiter que les n premières règles (ex: make ingestion LIMIT=5)
ingestion:
	uv run python scripts/ingestion.py $(if $(LIMIT),--limit $(LIMIT),)
	$(MAKE) export_sql

## Vide les tables Opquast de la base de données (utile pour retester une ingestion)
clear:
	uv run python scripts/clear_opquast_tables.py

## Exporte les données du RÉFÉRENTIEL uniquement — le domaine audit a sa
## propre base et n'est pas couvert ici. Avant la scission du 2026-09-08,
## cette cible dumpait toute la base : « sauvegarder le référentiel »
## sauvegardait aussi les audits, et une restauration les ramenait en
## arrière. Voir jury/decisions/2026-09-08-deux-bases-referentiel-audit.md
export_sql:
	mkdir -p backups
	@FILE="backups/$$(date +%Y%m%d_%H%M%S).sql"; \
	docker exec qualicheck-postgres pg_dump -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep '^POSTGRES_DB=' .env | cut -d= -f2)" --data-only --exclude-table=alembic_version --exclude-table=etat_donnees > "$$FILE"; \
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep '^POSTGRES_DB=' .env | cut -d= -f2)" -c "INSERT INTO etat_donnees (id, fichier_backup, type_operation, horodatage) VALUES (1, '$$FILE', 'export', now()) ON CONFLICT (id) DO UPDATE SET fichier_backup = EXCLUDED.fichier_backup, type_operation = EXCLUDED.type_operation, horodatage = EXCLUDED.horodatage;" > /dev/null; \
	echo "Export terminé : $$FILE"

## Importe un dump de RÉFÉRENTIEL généré par make export_sql. Ne vide rien
## avant restauration : si des lignes existent déjà, les conflits de clé
## primaire remontent. Ne concerne pas le domaine audit.
import_sql:
	@test -n "$(FILE)" || (echo "Usage : make import_sql FILE=backups/xxx.sql" && exit 1)
	docker exec -i qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep '^POSTGRES_DB=' .env | cut -d= -f2)" < $(FILE)
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep '^POSTGRES_DB=' .env | cut -d= -f2)" -c "INSERT INTO etat_donnees (id, fichier_backup, type_operation, horodatage) VALUES (1, '$(FILE)', 'import', now()) ON CONFLICT (id) DO UPDATE SET fichier_backup = EXCLUDED.fichier_backup, type_operation = EXCLUDED.type_operation, horodatage = EXCLUDED.horodatage;" > /dev/null
	@echo "Import terminé depuis $(FILE)"

## Relance le LLM sur les règles marquées review_status = a_revoir,
## en tenant compte de review_note, puis sauvegarde les données réelles
enrich-again:
	$(MAKE) export_sql
	uv run python scripts/enrich_again.py
	$(MAKE) export_sql

## Recalcule l'embedding de toutes les règles (modèle et dimension définis
## dans app/ingestion/manifest.yml, rôle embedding), puis sauvegarde les
## données réelles
embed-rules:
	uv run python scripts/embed_rules.py
	$(MAKE) export_sql

## Rejoue le jeu d'acceptance RAG (tests/acceptance/rag_acceptance.jsonl) :
## appel réel à l'API embeddings, coût réel, volontairement hors CI
rag-acceptance:
	uv run python scripts/check_rag_acceptance.py

## Compare le recall du RAG sur plusieurs top_n (3/5/10/15), rapport Markdown
rag-dense-acceptance:
	uv run python scripts/rag_dense_acceptance.py

## Mesure les scores (top-1, écart top-1/top-15) : sans_reponse vs cas PASS,
## pour trancher si un seuil relatif est calibrable (Temps 1 du chantier refus)
mesure-scores-refus:
	uv run python scripts/mesure_scores_refus.py

## Mesure MRR/recall@k pour 12 variantes de chunk (11 champs isoles +
## baseline) sur les 114 cas d'acceptance — vague 1 du protocole de mesure
mesure-variantes-chunks:
	uv run python scripts/mesure_variantes_chunks.py

## Mesure MRR/recall@k pour 6 candidats (baseline + 5 combinaisons de
## champs), jeu reserve stratifie + critere de decision — vague 2
mesure-combinaisons-chunks:
	uv run python scripts/mesure_combinaisons_chunks.py

## Mesure MRR/recall@k pour un candidat a 3 vecteurs par regle (complet +
## intitule + guide_analyse, fusionnes) contre la baseline — vague 3
mesure-multi-vecteurs-chunks:
	uv run python scripts/mesure_multi_vecteurs_chunks.py

## Mesure si un LLM classe correctement une question dans/hors perimetre
## Opquast SANS voir de candidats retrieval (hypothese guardrail agent)
mesure-guardrail-perimetre:
	uv run python scripts/mesure_guardrail_perimetre.py

# ============================================================
# API données
# ============================================================

# Port lu dans le manifeste, seule source de vérité.
API_REGLES_PORT = $(shell grep 'port:' app/api_regles/manifest.yml | tr -d ' ' | cut -d: -f2)

## Démarre l'API données en développement (rechargement automatique)
api-regles:
	uv run uvicorn app.api_regles.main:app --reload --port $(API_REGLES_PORT)

## Rejoue le jeu d'acceptance de l'API données (tests/acceptance/api_regles_acceptance.jsonl) :
## nécessite make api-regles démarré dans un autre terminal. Aucun appel LLM,
## mais UN PATCH réel réversible sur POSTGRES_DB (pas POSTGRES_TEST_DB) pour
## vérifier la boucle de revue de bout en bout — exception volontaire et
## documentée, voir docs/superpowers/plans/2026-07-26-api-regles-implementation.md
api-regles-acceptance:
	uv run python scripts/check_api_regles_acceptance.py

## Rejoue le jeu d'acceptance RAG (99 cas, tests/acceptance/rag_acceptance.jsonl)
## via POST /regles/dense en HTTP reel — necessite make api-regles demarre
## dans un autre terminal. Cout reel (LLM + embedding) a chaque execution,
## volontairement hors CI, comme make rag-acceptance.
api-regles-dense-acceptance:
	uv run python scripts/check_api_regles_dense_acceptance.py

# ============================================================
# Clients
# ============================================================

## Installe les dépendances npm du client de revue des règles
regles-api-client-install:
	cd clients/regles_api_client && npm install

## Démarre le serveur de développement du client de revue des règles
## (Vite, http://localhost:5173) — nécessite make api-regles démarré à part
regles-api-client:
	cd clients/regles_api_client && npm run dev

## Lance les tests (unitaires + acceptance) du client de revue des règles
regles-api-client-test:
	cd clients/regles_api_client && npm run test

# ============================================================
# Tests
# ============================================================

## Lance toute la suite de tests (nécessite qualicheck-postgres démarré, migration appliquée
## et make migration-test pour les tests d'intégration destructeurs)
test:
	uv run pytest tests/ -v

## Lance uniquement les tests unitaires (aucune BDD requise)
test-unit:
	uv run pytest tests/unit -v

## Lance uniquement les tests d'intégration (nécessite qualicheck-postgres démarré,
## migration appliquée et make migration-test pour les tests destructeurs)
test-integration:
	uv run pytest tests/integration -v

## Lance uniquement les tests de migration (nécessite qualicheck-postgres démarré
## et migration appliquée)
test-migration:
	uv run pytest tests/migration -v

# ============================================================
# Accès direct à la BDD
# ============================================================

## Ouvre une session psql interactive dans le conteneur Postgres
psql:
	docker exec -it qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep '^POSTGRES_DB=' .env | cut -d= -f2)"
