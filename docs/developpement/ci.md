# CI / CD


`.github/workflows/ci-feature.yml` — déclenché sur push sur toute branche sauf `main`/`dev`/`staging` (branches de travail type `feature`). Étapes : `uv sync` → `ruff check` → `scripts/migration.py` (contre un service `pgvector/pgvector:pg17` éphémère, pour vérifier que les migrations s'appliquent) → `pytest tests/unit tests/integration`.

- **Secrets BDD** (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) gérés via **GitHub Secrets**, pas via `.env` — le `.env` reste strictement local, jamais commité ; les secrets CI sont une configuration séparée côté GitHub. `POSTGRES_TEST_DB` du workflow réutilise volontairement la valeur du secret `POSTGRES_DB` (aucun secret dédié créé) — la base du service CI étant déjà éphémère à chaque run, cette réutilisation ne recrée pas le risque de l'incident du 2026-07-25.
- Le CI n'exécute **pas** `scripts/ingestion.py` (évite de vrais appels LLM facturés à chaque push) — les tests couvrent le code applicatif (unitaire + intégration), pas le pipeline d'ingestion réel.
- `tests/migration/` (et un futur `tests/acceptance/`) sont volontairement exclus de ce workflow — scope de tests plus léger pour une branche de travail. Réservés à un futur workflow dédié `dev`/`staging` (pas encore écrit, ces branches n'existent pas encore) avec une suite plus complète avant promotion.
