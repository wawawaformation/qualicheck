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
| `make export_sql` | Exporte les données réelles (`pg_dump --data-only`, hors `alembic_version`/`etat_donnees`) dans `backups/YYYYMMDD_HHMMSS.sql` (dossier gitignoré) — à lancer avant toute ré-ingestion réelle coûteuse ; met aussi à jour la table `etat_donnees` (fichier, opération, horodatage) |
| `make import_sql FILE=...` | Restaure un dump `export_sql` dans la base réelle — `FILE=` obligatoire ; échoue explicitement en cas de conflit de clé primaire (ne vide rien tout seul, voir `make clear` si besoin) ; met aussi à jour `etat_donnees` |
| `make enrich-again` | Rappelle le LLM sur les règles `review_status = a_revoir`/`invalide` (tient compte de `review_note`), vide ces champs après correction — `make export_sql` avant (backup pré-run) et après |
| `make embed-rules` | Recalcule l'embedding de toutes les règles (modèle et dimension définis dans `app/ingestion/manifest.yml`, rôle `embedding`), puis `make export_sql` |
| `make test` | Lance toute la suite (`pytest tests/`) — nécessite les conteneurs démarrés, les migrations appliquées, et `make migration-test` pour les tests d'intégration destructeurs |
| `make test-unit` | Lance uniquement `tests/unit` — aucune BDD requise |
| `make test-integration` | Lance uniquement `tests/integration` — nécessite `make migration-test` pour les tests destructeurs |
| `make test-migration` | Lance uniquement `tests/migration` — nécessite les migrations appliquées |
| `make psql` | Ouvre une session `psql` interactive dans le conteneur Postgres |
| `make api-regles` | Démarre l'API données en dev (`app/api_regles`, port lu dans `app/api_regles/config.yml`, 8880) |
| `make api-business` | Démarre l'API business en dev (`app/agent_us2`, `POST /questions`, port lu dans `app/agent_us2/config.yml`, 8882) |

À jour ici pour référence rapide, mais le `Makefile` lui-même reste la source de vérité — le relire directement en cas de doute plutôt que de se fier uniquement à ce tableau.