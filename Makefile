.PHONY: up down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again

# ============================================================
# Docker
# ============================================================

## Démarre tous les conteneurs Docker (construit les images si nécessaire)
up:
	docker compose up -d --build

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
	docker exec qualicheck-postgres pg_dump -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" --data-only --exclude-table=alembic_version > "$$FILE"; \
	echo "Export terminé : $$FILE"

## Importe un dump généré par make export_sql dans la base réelle.
## FILE=backups/xxx.sql obligatoire. Ne vide rien avant restauration : si des
## lignes existent déjà, psql échoue sur les conflits de clé primaire — lancer
## make clear avant si besoin.
import_sql:
	@test -n "$(FILE)" || (echo "Usage : make import_sql FILE=backups/xxx.sql" && exit 1)
	docker exec -i qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$$(grep POSTGRES_DB .env | cut -d= -f2)" < $(FILE)
	@echo "Import terminé depuis $(FILE)"

## Relance le LLM sur les règles marquées review_status = a_revoir/invalide,
## en tenant compte de review_note, puis sauvegarde les données réelles
enrich-again:
	$(MAKE) export_sql
	uv run python scripts/enrich_again.py
	$(MAKE) export_sql

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
