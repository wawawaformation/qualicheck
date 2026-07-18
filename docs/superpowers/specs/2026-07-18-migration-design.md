# Design — Migration (Alembic + modèles SQLAlchemy)

**Date :** 2026-07-18  
**Phase :** feature (avant dev et main)  
**Périmètre :** modèles SQLAlchemy, configuration Alembic, première migration, point d'entrée CLI

---

## Contexte

Deuxième brique technique de QualiCheck, prérequis à l'ingestion. Crée le schéma complet en base (vide), à partir du MLD (`conception/2_ingestion/MLD_qualicheck.md`). Ne peuple aucune donnée.

Déclenchement : manuel, via `uv run python scripts/migration.py`.

---

## Structure des fichiers

```
pyproject.toml                          ← ajout des dépendances
app/
  __init__.py
  models/
    __init__.py
    base.py                             ← Base SQLAlchemy (DeclarativeBase)
    referentiel.py                      ← tables Opquast : theme, regle, objectif, phase, tag + associations
    metier.py                           ← tables métier : utilisateur, audit, page, audit_page, audit_regle, constat
  migration/
    alembic.ini                         ← config Alembic (connexion BDD, chemin des versions)
    env.py                              ← point d'entrée Alembic, importe Base depuis app/models/
    versions/
      0001_schema_initial.py            ← CREATE EXTENSION vector, toutes les tables, 3 index
scripts/
  migration.py                          ← subprocess : alembic upgrade head
```

---

## Dépendances Python

Ajoutées via `uv add` dans `pyproject.toml` :

| Paquet | Rôle |
|---|---|
| `sqlalchemy` | ORM — déclaration des modèles |
| `alembic` | Gestion des migrations |
| `psycopg2-binary` | Driver PostgreSQL pour Python |
| `pgvector` | Type `Vector` pour SQLAlchemy/Alembic |
| `python-dotenv` | Lecture du `.env` dans `env.py` |

---

## app/models/base.py

Déclare uniquement `Base = DeclarativeBase()`. Importée par `referentiel.py`, `metier.py` et `env.py`. Point de convergence unique — pas de duplication.

---

## app/models/referentiel.py

Tables du référentiel Opquast, dérivées du MLD :

- `theme` : id (PK), theme (VARCHAR 64, UNIQUE, NOT NULL)
- `regle` : id (PK), theme_id (FK), numero (UNIQUE), intitule, solution, controle, strategie_analyse, strategie_justification, strategie_source, strategie_score (DECIMAL 3,2), guide_analyse, llm_provider, embedding (Vector 384)
- `objectif` : id (PK), objectif (VARCHAR 256, NOT NULL)
- `phase` : id (PK), phase (VARCHAR 64, NOT NULL)
- `tag` : id (PK), tag (VARCHAR 50, NOT NULL)
- `objectif_regle` : table d'association (objectif_id, regle_id) — PK composite
- `phase_regle` : table d'association (phase_id, regle_id) — PK composite
- `regle_tag` : table d'association (regle_id, tag_id) — PK composite

---

## app/models/metier.py

Tables du cœur métier QualiCheck, dérivées du MLD :

- `utilisateur` : id (PK), nom (VARCHAR 64), prenom (VARCHAR 64)
- `audit` : id (PK), utilisateur_id (FK), url_depart (VARCHAR 512), statut (VARCHAR 50), date_creation (DATETIME), date_modification (DATETIME nullable)
- `page` : id (PK), url (VARCHAR 512), titre (VARCHAR 255 nullable)
- `audit_page` : audit_id (FK), page_id (FK) — PK composite, statut_http, est_selectionnee (BOOLEAN), date_crawl (DATETIME nullable)
- `audit_regle` : audit_id (FK), regle_id (FK) — PK composite
- `constat` : audit_id (FK), page_id (FK), regle_id (FK) — PK composite, statut (VARCHAR 32), commentaire, recommandation, preuve, validation_humaine (BOOLEAN nullable), feedback_auditeur (TEXT nullable)

---

## app/migration/alembic.ini

- `script_location` : chemin vers `app/migration/`
- `sqlalchemy.url` : laissé vide — construit dynamiquement dans `env.py` depuis le `.env`

---

## app/migration/env.py

- Charge le `.env` via `python-dotenv`
- Construit l'URL de connexion depuis les variables `POSTGRES_*`
- Importe `Base` depuis `app/models/base.py` — fournit `target_metadata` à Alembic
- Mode offline non utilisé (MVP, connexion directe toujours disponible)

---

## app/migration/versions/0001_schema_initial.py

Contenu de `upgrade()` dans l'ordre :

1. `CREATE EXTENSION IF NOT EXISTS vector` — pgvector, prérequis à la colonne `embedding`
2. Création des tables dans l'ordre des dépendances FK : `theme`, `objectif`, `phase`, `tag`, `utilisateur`, `regle`, `objectif_regle`, `phase_regle`, `regle_tag`, `page`, `audit`, `audit_page`, `audit_regle`, `constat`
3. Index HNSW : `CREATE INDEX ON regle USING hnsw (embedding vector_cosine_ops)`
4. Index B-tree : `CREATE INDEX ON constat (audit_id)`, `CREATE INDEX ON audit_regle (audit_id)`

Contenu de `downgrade()` : suppression des index puis des tables dans l'ordre inverse, puis `DROP EXTENSION IF EXISTS vector`.

---

## scripts/migration.py

Lance `alembic upgrade head` via `subprocess.run`, en positionnant le répertoire de travail sur `app/migration/` pour qu'Alembic trouve son `alembic.ini`. Retourne le code de sortie d'Alembic — non-nul en cas d'erreur.

---

## Ce que ce design ne couvre pas

- Mode offline Alembic (non nécessaire en MVP)
- Migrations futures (évolutions post-MVP du schéma)
- Autogenerate Alembic (la migration est écrite à la main — plus lisible et pédagogique)
