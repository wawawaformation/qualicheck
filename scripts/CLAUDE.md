# scripts/

Uniquement les points d'entrée, à plat. Aucune logique métier ici, aucun sous-dossier — l'orchestration appelle les modules situés dans `app/`.

## Fichiers

- **`migration.py`** : déclenche la montée de version Alembic. Logique et configuration dans `app/migration/`. Détail : `conception/1_BDD/bdd.md`.
- **`ingestion.py`** : orchestre les 7 étapes du pipeline d'ingestion en séquence (acquisition → agrégation → enrichissement → stockage → chunking → embedding → indexation), applique le principe fail-fast, écrit les logs. Modules dans `app/ingestion/`. Détail : `conception/2_ingestion/ingestion.md`.

## Changelog

Toute modification d'un point d'entrée ou de ses modules de support (`app/migration/`, `app/ingestion/`) est déclarée dans `CHANGELOG.md` à la racine — voir `CLAUDE.md` racine pour le format.
