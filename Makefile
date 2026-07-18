.PHONY: up down migration downgrade test

## Démarre tous les conteneurs Docker (construit les images si nécessaire)
up:
	docker compose up -d --build

## Éteint tous les conteneurs Docker
down:
	docker compose down

## Applique les migrations Alembic (crée le schéma BDD)
migration:
	uv run python scripts/migration.py

## Supprime toutes les tables (downgrade Alembic) — permet de retester une migration from scratch
downgrade:
	cd app/migration && uv run alembic downgrade base

## Lance les tests d'intégration (nécessite qualicheck-postgres démarré et migration appliquée)
test:
	uv run pytest tests/ -v
