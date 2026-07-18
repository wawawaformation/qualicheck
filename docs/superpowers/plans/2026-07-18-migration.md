# Migration — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Créer le schéma BDD complet (vide) via Alembic — modèles SQLAlchemy, configuration Alembic, première migration, point d'entrée CLI.

**Architecture :** `scripts/migration.py` appelle `alembic upgrade head` en subprocess. Les modèles SQLAlchemy vivent dans `app/models/` (partagés avec le futur backend FastAPI). Alembic est configuré dans `app/migration/` et importe `Base` depuis `app/models/base.py`.

**Tech Stack :** Python, SQLAlchemy, Alembic, psycopg2-binary, pgvector, python-dotenv, uv

## Global Constraints

- Déclenchement manuel uniquement : `uv run python scripts/migration.py`
- Migration écrite à la main (pas d'autogenerate Alembic)
- MLD source de vérité : `conception/2_ingestion/MLD_qualicheck.md`
- Un seul `.env` à la racine, jamais versionné
- `app/models/base.py` est le seul endroit où `Base` est déclarée
- Pas de commit/push sans validation explicite de l'utilisateur

---

### Task 1 : Dépendances Python

**Files :**
- Modifier : `pyproject.toml`

**Interfaces :**
- Produit : environnement Python avec `sqlalchemy`, `alembic`, `psycopg2-binary`, `pgvector`, `python-dotenv`

- [ ] **Étape 1 : Ajouter les dépendances via uv**

```bash
uv add sqlalchemy alembic psycopg2-binary pgvector python-dotenv
```

- [ ] **Étape 2 : Vérifier que les paquets sont bien installés**

```bash
uv run python -c "import sqlalchemy, alembic, psycopg2, pgvector, dotenv; print('OK')"
```

Résultat attendu : `OK`

- [ ] **Étape 3 : Vérifier le contenu de pyproject.toml**

```bash
cat pyproject.toml
```

Résultat attendu : les 5 paquets apparaissent dans `dependencies`.

---

### Task 2 : Modèles SQLAlchemy — base et référentiel

**Files :**
- Créer : `app/__init__.py`
- Créer : `app/models/__init__.py`
- Créer : `app/models/base.py`
- Créer : `app/models/referentiel.py`

**Interfaces :**
- Produit : `Base` (depuis `app/models/base.py`), classes `Theme`, `Regle`, `Objectif`, `Phase`, `Tag`, `ObjectifRegle`, `PhaseRegle`, `RegleTag`

- [ ] **Étape 1 : Créer `app/__init__.py`** (vide)

```python
```

- [ ] **Étape 2 : Créer `app/models/__init__.py`** (vide)

```python
```

- [ ] **Étape 3 : Créer `app/models/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Étape 4 : Créer `app/models/referentiel.py`**

```python
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, ForeignKey, PrimaryKeyConstraint
)
from pgvector.sqlalchemy import Vector
from app.models.base import Base


class Theme(Base):
    __tablename__ = "theme"

    id = Column(Integer, primary_key=True)
    theme = Column(String(64), nullable=False, unique=True)


class Regle(Base):
    __tablename__ = "regle"

    id = Column(Integer, primary_key=True)
    theme_id = Column(Integer, ForeignKey("theme.id"), nullable=False)
    numero = Column(Integer, nullable=False, unique=True)
    intitule = Column(String(512), nullable=False)
    solution = Column(String(512), nullable=False)
    controle = Column(String(512), nullable=False)
    strategie_analyse = Column(String(20), nullable=False)
    strategie_justification = Column(Text)
    strategie_source = Column(String(20), nullable=False)
    strategie_score = Column(Numeric(3, 2))
    guide_analyse = Column(Text, nullable=False)
    llm_provider = Column(String(20))
    embedding = Column(Vector(384))


class Objectif(Base):
    __tablename__ = "objectif"

    id = Column(Integer, primary_key=True)
    objectif = Column(String(256), nullable=False)


class Phase(Base):
    __tablename__ = "phase"

    id = Column(Integer, primary_key=True)
    phase = Column(String(64), nullable=False)


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False)


class ObjectifRegle(Base):
    __tablename__ = "objectif_regle"

    objectif_id = Column(Integer, ForeignKey("objectif.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("objectif_id", "regle_id"),
    )


class PhaseRegle(Base):
    __tablename__ = "phase_regle"

    phase_id = Column(Integer, ForeignKey("phase.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("phase_id", "regle_id"),
    )


class RegleTag(Base):
    __tablename__ = "regle_tag"

    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("regle_id", "tag_id"),
    )
```

- [ ] **Étape 5 : Vérifier que les modèles s'importent sans erreur**

```bash
uv run python -c "from app.models.referentiel import Theme, Regle, Objectif, Phase, Tag; print('OK')"
```

Résultat attendu : `OK`

---

### Task 3 : Modèles SQLAlchemy — métier

**Files :**
- Créer : `app/models/metier.py`

**Interfaces :**
- Consomme : `Base` depuis `app/models/base.py`
- Produit : classes `Utilisateur`, `Audit`, `Page`, `AuditPage`, `AuditRegle`, `Constat`

- [ ] **Étape 1 : Créer `app/models/metier.py`**

```python
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint
)
from app.models.base import Base


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id = Column(Integer, primary_key=True)
    nom = Column(String(64), nullable=False)
    prenom = Column(String(64), nullable=False)


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    url_depart = Column(String(512), nullable=False)
    statut = Column(String(50), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    date_modification = Column(DateTime)


class Page(Base):
    __tablename__ = "page"

    id = Column(Integer, primary_key=True)
    url = Column(String(512), nullable=False)
    titre = Column(String(255))


class AuditPage(Base):
    __tablename__ = "audit_page"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("page.id"), nullable=False)
    statut_http = Column(String(10))
    est_selectionnee = Column(Boolean, nullable=False)
    date_crawl = Column(DateTime)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "page_id"),
    )


class AuditRegle(Base):
    __tablename__ = "audit_regle"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "regle_id"),
    )


class Constat(Base):
    __tablename__ = "constat"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("page.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)
    statut = Column(String(32), nullable=False)
    commentaire = Column(String(512))
    recommandation = Column(String(512))
    preuve = Column(String(512))
    validation_humaine = Column(Boolean)
    feedback_auditeur = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )
```

- [ ] **Étape 2 : Vérifier que les modèles s'importent sans erreur**

```bash
uv run python -c "from app.models.metier import Utilisateur, Audit, Page, AuditPage, AuditRegle, Constat; print('OK')"
```

Résultat attendu : `OK`

---

### Task 4 : Configuration Alembic

**Files :**
- Créer : `app/migration/__init__.py`
- Créer : `app/migration/alembic.ini`
- Créer : `app/migration/env.py`
- Créer : `app/migration/versions/__init__.py`

**Interfaces :**
- Consomme : `Base` depuis `app/models/base.py`, variables `POSTGRES_*` depuis `.env`
- Produit : Alembic configuré et fonctionnel, prêt à générer/appliquer des migrations

- [ ] **Étape 1 : Créer `app/migration/__init__.py`** (vide)

```python
```

- [ ] **Étape 2 : Créer `app/migration/versions/__init__.py`** (vide)

```python
```

- [ ] **Étape 3 : Créer `app/migration/alembic.ini`**

```ini
[alembic]
# chemin vers le dossier contenant env.py et versions/
script_location = .

# l'URL est construite dynamiquement dans env.py — laisser vide ici
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Étape 4 : Créer `app/migration/env.py`**

```python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from alembic import context
from sqlalchemy import engine_from_config, pool

# -- Résolution des chemins --------------------------------------------------
# env.py est exécuté par Alembic depuis app/migration/.
# On remonte à la racine du projet pour que "app.models" soit importable.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# -- Chargement du .env ------------------------------------------------------
load_dotenv(ROOT / ".env")

# -- Import des modèles (nécessaire pour target_metadata) --------------------
from app.models.base import Base  # noqa: E402
import app.models.referentiel  # noqa: E402, F401 — enregistre les tables dans Base
import app.models.metier        # noqa: E402, F401 — enregistre les tables dans Base

target_metadata = Base.metadata

# -- Construction de l'URL de connexion --------------------------------------
def get_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


# -- Mode online (connexion directe) -----------------------------------------
def run_migrations_online() -> None:
    configuration = context.config.get_section(context.config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

- [ ] **Étape 5 : Vérifier qu'Alembic reconnaît la configuration**

```bash
cd app/migration && uv run alembic current
```

Résultat attendu : `INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.` suivi de la version courante (vide à ce stade).

---

### Task 5 : Première migration

**Files :**
- Créer : `app/migration/versions/0001_schema_initial.py`

**Interfaces :**
- Consomme : PostgreSQL avec pgvector disponible (conteneur `qualicheck-postgres` démarré)
- Produit : schéma complet en base (toutes les tables du MLD + 3 index)

- [ ] **Étape 1 : Créer `app/migration/versions/0001_schema_initial.py`**

```python
"""Schéma initial — référentiel Opquast + cœur métier QualiCheck

Revision ID: 0001
Revises:
Create Date: 2026-07-18
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Extension pgvector (prérequis à la colonne embedding) ---------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # -- Référentiel Opquast -------------------------------------------------
    op.create_table(
        "theme",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("theme", sa.String(64), nullable=False, unique=True),
    )

    op.create_table(
        "objectif",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("objectif", sa.String(256), nullable=False),
    )

    op.create_table(
        "phase",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("phase", sa.String(64), nullable=False),
    )

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tag", sa.String(50), nullable=False),
    )

    op.create_table(
        "regle",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("theme_id", sa.Integer, sa.ForeignKey("theme.id"), nullable=False),
        sa.Column("numero", sa.Integer, nullable=False, unique=True),
        sa.Column("intitule", sa.String(512), nullable=False),
        sa.Column("solution", sa.String(512), nullable=False),
        sa.Column("controle", sa.String(512), nullable=False),
        sa.Column("strategie_analyse", sa.String(20), nullable=False),
        sa.Column("strategie_justification", sa.Text),
        sa.Column("strategie_source", sa.String(20), nullable=False),
        sa.Column("strategie_score", sa.Numeric(3, 2)),
        sa.Column("guide_analyse", sa.Text, nullable=False),
        sa.Column("llm_provider", sa.String(20)),
        sa.Column("embedding", Vector(384)),
    )

    op.create_table(
        "objectif_regle",
        sa.Column("objectif_id", sa.Integer, sa.ForeignKey("objectif.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("objectif_id", "regle_id"),
    )

    op.create_table(
        "phase_regle",
        sa.Column("phase_id", sa.Integer, sa.ForeignKey("phase.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("phase_id", "regle_id"),
    )

    op.create_table(
        "regle_tag",
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id"), nullable=False),
        sa.PrimaryKeyConstraint("regle_id", "tag_id"),
    )

    # -- Cœur métier QualiCheck ----------------------------------------------
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
    )

    op.create_table(
        "audit",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("utilisateur_id", sa.Integer, sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime, nullable=False),
        sa.Column("date_modification", sa.DateTime),
    )

    op.create_table(
        "page",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255)),
    )

    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("page_id", sa.Integer, sa.ForeignKey("page.id"), nullable=False),
        sa.Column("statut_http", sa.String(10)),
        sa.Column("est_selectionnee", sa.Boolean, nullable=False),
        sa.Column("date_crawl", sa.DateTime),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )

    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("audit_id", "regle_id"),
    )

    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("page_id", sa.Integer, sa.ForeignKey("page.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512)),
        sa.Column("recommandation", sa.String(512)),
        sa.Column("preuve", sa.String(512)),
        sa.Column("validation_humaine", sa.Boolean),
        sa.Column("feedback_auditeur", sa.Text),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )

    # -- Index ---------------------------------------------------------------
    # HNSW : recherche sémantique RAG (pgvector)
    op.execute("CREATE INDEX ON regle USING hnsw (embedding vector_cosine_ops)")
    # B-tree : performances sur les constats et règles d'un audit
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])


def downgrade() -> None:
    # -- Index ---------------------------------------------------------------
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.execute("DROP INDEX IF EXISTS regle_embedding_idx")

    # -- Tables (ordre inverse des FK) ---------------------------------------
    op.drop_table("constat")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")
    op.drop_table("regle_tag")
    op.drop_table("phase_regle")
    op.drop_table("objectif_regle")
    op.drop_table("regle")
    op.drop_table("tag")
    op.drop_table("phase")
    op.drop_table("objectif")
    op.drop_table("theme")

    # -- Extension -----------------------------------------------------------
    op.execute("DROP EXTENSION IF EXISTS vector")
```

---

### Task 6 : Point d'entrée `scripts/migration.py`

**Files :**
- Créer : `scripts/migration.py`

**Interfaces :**
- Consomme : Alembic configuré dans `app/migration/`
- Produit : exécution de `alembic upgrade head` via subprocess

- [ ] **Étape 1 : Créer `scripts/migration.py`**

```python
"""Point d'entrée pour appliquer les migrations Alembic.

Lance `alembic upgrade head` depuis app/migration/ via subprocess.
Retourne le code de sortie d'Alembic (0 = succès, non-nul = erreur).
"""
import subprocess
import sys
from pathlib import Path

# Répertoire contenant alembic.ini
MIGRATION_DIR = Path(__file__).resolve().parents[1] / "app" / "migration"


def main() -> None:
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=MIGRATION_DIR,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

- [ ] **Étape 2 : S'assurer que le conteneur PostgreSQL est démarré**

```bash
docker compose ps
```

Résultat attendu : `qualicheck-postgres` avec status `running`.

- [ ] **Étape 3 : Lancer la migration**

```bash
uv run python scripts/migration.py
```

Résultat attendu :
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Schéma initial
```

- [ ] **Étape 4 : Vérifier les tables en base**

```bash
docker compose exec postgres psql -U qualicheck -d qualicheck -c "\dt"
```

Résultat attendu : liste des 14 tables (`theme`, `regle`, `objectif`, `phase`, `tag`, `objectif_regle`, `phase_regle`, `regle_tag`, `utilisateur`, `audit`, `page`, `audit_page`, `audit_regle`, `constat`) + table `alembic_version`.

- [ ] **Étape 5 : Vérifier l'index HNSW**

```bash
docker compose exec postgres psql -U qualicheck -d qualicheck -c "\di regle*"
```

Résultat attendu : un index de type `hnsw` sur `regle`.

- [ ] **Étape 6 : Vérifier que la migration est idempotente (relance)**

```bash
uv run python scripts/migration.py
```

Résultat attendu : `INFO  [alembic.runtime.migration] Running upgrade  -> 0001` n'apparaît pas — la migration est déjà appliquée, Alembic ne fait rien.
