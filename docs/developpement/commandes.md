# Makefile

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
| `make embed-rules` | Recalcule l'embedding de toutes les règles (modèle et dimension définis dans `app/ingestion/manifest.yml`, rôle `embedding`), puis `make export_sql` |
| `make test` | Lance toute la suite (`pytest tests/`) — nécessite les conteneurs démarrés, les migrations appliquées, et `make migration-test` pour les tests d'intégration destructeurs |
| `make test-unit` | Lance uniquement `tests/unit` — aucune BDD requise |
| `make test-integration` | Lance uniquement `tests/integration` — nécessite `make migration-test` pour les tests destructeurs |
| `make test-migration` | Lance uniquement `tests/migration` — nécessite les migrations appliquées |
| `make psql` | Ouvre une session `psql` interactive dans le conteneur Postgres |

À jour ici pour référence rapide, mais le `Makefile` lui-même reste la source de vérité — le relire directement en cas de doute plutôt que de se fier uniquement à ce tableau.