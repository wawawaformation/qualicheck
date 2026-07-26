# Contexte projet QualiCheck

Projet de certification IA agentique, basé sur un audit qualité web Opquast (245 règles).

## Finalité

Le projet doit être défendable devant jury : chaque choix doit être explicable, pas seulement fonctionnel.

## Stack

- Backend : FastAPI (Python)
- Frontend : Vue.js
- Données : PostgreSQL + pgvector
- Migrations : Alembic
- Environnement Python : uv
- Lint : Ruff
- Exécution : Docker + docker-compose

## Pipeline actuel

1. scripts/migration.py : crée/met à jour le schéma
2. scripts/ingestion.py : exécute le pipeline d’ingestion Opquast
3. US audit/question libre : non finalisées à ce stade

## Point de vigilance coût

Les appels LLM sont facturés. Éviter toute ré-ingestion complète non nécessaire.

## Principes opérationnels clés

- Retry LLM : 3 tentatives avec backoff
- Approche spec-driven : spec validée avant implémentation
- Risque principal : dérive entre spec et code (spec drift)
