.PHONY: up up-db down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again embed-rules rag-acceptance api-regles api-regles-acceptance client-revue

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

## Éteint tous les conteneurs Docker
down:
	docker compose down

# ============================================================
# Migrations (Alembic)
# ============================================================

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
		"SELECT 1 FROM pg_database WHERE datname = '$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)'" | grep -q 1 || \
		docker exec qualicheck-postgres createdb -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" "$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)"
	POSTGRES_DB="$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)" uv run python scripts/migration.py

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

## Exporte les données réelles (pg_dump --data-only, hors alembic_version)
## dans backups/YYYYMMDD_HHMMSS.sql — à lancer avant toute ré-ingestion
## réelle coûteuse
export_sql:
	mkdir -p backups
	@FILE="backups/$$(date +%Y%m%d_%H%M%S).sql"; \
	docker exec qualicheck-postgres pg_dump -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" --data-only --exclude-table=alembic_version --exclude-table=etat_donnees > "$$FILE"; \
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" -c "INSERT INTO etat_donnees (id, fichier_backup, type_operation, horodatage) VALUES (1, '$$FILE', 'export', now()) ON CONFLICT (id) DO UPDATE SET fichier_backup = EXCLUDED.fichier_backup, type_operation = EXCLUDED.type_operation, horodatage = EXCLUDED.horodatage;" > /dev/null; \
	echo "Export terminé : $$FILE"

## Importe un dump généré par make export_sql dans la base réelle.
## FILE=backups/xxx.sql obligatoire. Ne vide rien avant restauration : si des
## lignes existent déjà, psql échoue sur les conflits de clé primaire — lancer
## make clear avant si besoin.
import_sql:
	@test -n "$(FILE)" || (echo "Usage : make import_sql FILE=backups/xxx.sql" && exit 1)
	docker exec -i qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" < $(FILE)
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" -c "INSERT INTO etat_donnees (id, fichier_backup, type_operation, horodatage) VALUES (1, '$(FILE)', 'import', now()) ON CONFLICT (id) DO UPDATE SET fichier_backup = EXCLUDED.fichier_backup, type_operation = EXCLUDED.type_operation, horodatage = EXCLUDED.horodatage;" > /dev/null
	@echo "Import terminé depuis $(FILE)"

## Relance le LLM sur les règles marquées review_status = a_revoir/invalide,
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

# ============================================================
# Client de revue
# ============================================================

## Sert le client léger de revue humaine sur http://localhost:5173
client-revue:
	python3 -m http.server 5173 --directory client_revue

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
	docker exec -it qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)"
