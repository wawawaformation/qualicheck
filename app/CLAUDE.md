# app/

Domaine métier et modules de support. Importé par `scripts/`, jamais l'inverse.

## Sous-dossiers conçus à ce stade

- **`models/`** : déclaration SQLAlchemy des tables (dérivées de `conception/1_BDD/MLD_qualicheck.md`). Possédé par le backend — source de vérité du domaine métier, importée aussi bien par `app/migration/` (génération des migrations) que par le futur backend FastAPI. Ne pas dupliquer ailleurs. Exception : `etat.py` (table `etat_donnees`) est une table de bookkeeping opérationnel (provenance du dernier export/import de backup), pas issue du MLD — mise à jour directement par les cibles Makefile `export_sql`/`import_sql`, pas par du code applicatif.
- **`migration/`** : configuration et migrations Alembic (`alembic.ini`, `env.py`, `versions/`). Détail et justification des choix : `conception/1_BDD/bdd.md`.
- **`ingestion/`** : modules du pipeline d'ingestion — `acquisition.py`, `aggregation.py`, `enrichment.py`, `stockage.py`, `chunking.py`, `embedding.py`, `enrich_again.py` (réécriture ciblée des règles à revoir). Détail et justification des choix : `conception/2_us0/ingestion/ingestion.md`.

## Non conçu à ce stade

Le reste de `app/` (API FastAPI, services d'audit, dialogue, question libre...) n'a pas encore été conçu — ne pas anticiper de structure ici tant que la conception correspondante n'existe pas dans `conception/`.

## Changelog

Toute création ou modification de fichier sous `app/` est déclarée dans `CHANGELOG.md` à la racine — voir `CLAUDE.md` racine pour le format.
