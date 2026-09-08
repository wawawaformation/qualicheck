# Scission en deux bases (référentiel / audit) — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal :** séparer le référentiel Opquast et les données d'audit en deux bases
PostgreSQL distinctes, pour que la frontière entre étages devienne une
contrainte et non une convention.

**Architecture :** deux bases dans la même instance PostgreSQL. La base
existante (`qualicheck`) devient celle du référentiel — les 245 règles ne
bougent pas. Une base `qualicheck_audit` est créée vide et reçoit les six
tables métier, dont les deux liens vers `regle` deviennent un `regle_numero`
sans clé étrangère. Deux bases déclaratives SQLAlchemy et deux chaînes
Alembic remplacent l'unique jeu actuel.

**Tech Stack :** PostgreSQL 17 + pgvector, SQLAlchemy 2 (`DeclarativeBase`),
Alembic, psycopg2, FastAPI, pytest, uv, Ruff, Docker Compose.

**Spec :** `docs/superpowers/specs/2026-09-08-scission-bases-design.md`
**Décision :** `jury/decisions/2026-09-08-deux-bases-referentiel-audit.md`

## Global Constraints

- **Les 245 règles et leurs vecteurs doivent rester intacts après chaque
  tâche.** Vérification : `SELECT count(*) FROM regle` = 245 et
  `count(*) FILTER (WHERE embedding IS NOT NULL)` = 245.
- **Aucun test destructeur ne cible une base de développement.** Les tests
  d'intégration passent par `POSTGRES_TEST_DB` / `POSTGRES_TEST_DB_AUDIT`.
  Exception existante et volontaire : `tests/migration/` lit les bases de
  développement, en lecture seule uniquement.
- **Code en anglais, commentaires et docstrings en français.**
- `ruff check` doit rester vert (`uv run ruff check`).
- **Un seul mécanisme de création de base**, réutilisé localement et en CI —
  pas de script d'init Docker en parallèle.
- **Hors périmètre, ne rien construire** : `GET /dense`, `app/api_audit`, la
  sauvegarde du domaine audit, la validation applicative du `regle_numero`.
- Toute tâche terminée est tracée dans `CHANGELOG.md` (format
  `## [date] — [outil]`).

## File Structure

| Fichier | Responsabilité |
| --- | --- |
| `app/models/base.py` (modifié) | Déclare les deux bases déclaratives, une par domaine |
| `app/models/referentiel.py` (modifié) | Hérite de `BaseReferentiel` — inchangé par ailleurs |
| `app/models/etat.py` (modifié) | Hérite de `BaseReferentiel` |
| `app/models/metier.py` (modifié) | Hérite de `BaseAudit` ; `regle_id` → `regle_numero`, sans FK |
| `app/db.py` (modifié) | Deux URL, deux moteurs, deux dépendances FastAPI nommées par domaine |
| `app/migration/env.py` (modifié) | Cible `BaseReferentiel` seul |
| `app/migration/versions/0013_drop_tables_metier.py` (créé) | Retire les six tables métier de la base du référentiel |
| `app/migration_audit/` (créé) | Chaîne Alembic du domaine audit (`alembic.ini`, `env.py`, `versions/0001_schema_audit.py`) |
| `scripts/create_db_audit.py` (créé) | Point d'entrée idempotent de création de la base d'audit |
| `scripts/migration.py` (modifié) | Accepte le domaine à migrer |
| `Makefile` (modifié) | Cibles par domaine ; `export_sql`/`import_sql` bornés au référentiel |
| `tests/unit/test_models_bases.py` (créé) | Prouve que les deux métadonnées sont disjointes et que le métier n'a plus de FK vers `regle` |
| `tests/unit/test_db.py` (modifié) | Les deux URL visent bien deux bases distinctes |
| `tests/migration/test_migration.py` (modifié) | Ne garde que les assertions du référentiel |
| `tests/migration/test_migration_audit.py` (créé) | Assertions du schéma d'audit + preuve d'isolation |
| `.env.example` (modifié) | `POSTGRES_DB_AUDIT`, `POSTGRES_TEST_DB_AUDIT` |
| `.gitea/workflows/ci-dev.yml` (modifié) | Crée et migre la base d'audit avant les tests |
| `conception/1_BDD/bdd.md`, `MLD_qualicheck.md`, `docs/rgpd/registre_traitements.md` (modifiés) | Source de vérité durable alignée sur deux bases |

---

### Task 1 : Deux bases déclaratives

**Files:**
- Modify: `app/models/base.py`
- Modify: `app/models/referentiel.py:1-15` (l'import de `Base`)
- Modify: `app/models/etat.py:3` (l'import de `Base`)
- Modify: `app/models/metier.py:12` (l'import de `Base`)
- Modify: `app/migration/env.py:18-23`
- Test: `tests/unit/test_models_bases.py`

**Interfaces:**
- Consumes: rien (première tâche).
- Produces: `app.models.base.BaseReferentiel` et `app.models.base.BaseAudit`,
  deux classes `DeclarativeBase`. `Base` **disparaît** — tout import de
  `app.models.base.Base` doit être remplacé.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/unit/test_models_bases.py` :

```python
"""
Les deux domaines ont chacun leur base déclarative.

Sans cette séparation, l'autogenerate de chaque chaîne Alembic verrait les
tables de l'autre domaine et proposerait de les supprimer.
"""

import app.models.etat  # noqa: F401 — enregistre etat_donnees
import app.models.metier  # noqa: F401 — enregistre les tables métier
import app.models.referentiel  # noqa: F401 — enregistre les tables du référentiel
from app.models.base import BaseAudit, BaseReferentiel

TABLES_REFERENTIEL = {
    "theme",
    "regle",
    "objectif",
    "phase",
    "tag",
    "objectif_regle",
    "phase_regle",
    "regle_tag",
    "etat_donnees",
}

TABLES_AUDIT = {
    "utilisateur",
    "audit",
    "page",
    "audit_page",
    "audit_regle",
    "constat",
}


def test_le_referentiel_ne_declare_que_ses_tables():
    assert set(BaseReferentiel.metadata.tables) == TABLES_REFERENTIEL


def test_le_domaine_audit_ne_declare_que_ses_tables():
    assert set(BaseAudit.metadata.tables) == TABLES_AUDIT


def test_les_deux_metadata_sont_disjointes():
    communes = set(BaseReferentiel.metadata.tables) & set(BaseAudit.metadata.tables)
    assert communes == set(), f"tables déclarées deux fois : {communes}"
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `uv run pytest tests/unit/test_models_bases.py -v`
Expected: FAIL — `ImportError: cannot import name 'BaseAudit' from 'app.models.base'`

- [ ] **Step 3: Remplacer `Base` par les deux bases**

`app/models/base.py`, contenu complet :

```python
from sqlalchemy.orm import DeclarativeBase


class BaseReferentiel(DeclarativeBase):
    """Schéma de la base du référentiel Opquast (245 règles, vecteurs)."""


class BaseAudit(DeclarativeBase):
    """Schéma de la base des données d'audit."""
```

- [ ] **Step 4: Réaffecter chaque modèle à sa base**

Dans `app/models/referentiel.py`, remplacer l'import et chaque déclaration de
classe :

```python
from app.models.base import BaseReferentiel
```

Puis, pour **chacune** des classes du fichier (`Theme`, `Regle`, `Objectif`,
`Phase`, `Tag`, `ObjectifRegle`, `PhaseRegle`, `RegleTag`) : remplacer
`(Base)` par `(BaseReferentiel)`.

Dans `app/models/etat.py` :

```python
from app.models.base import BaseReferentiel


class EtatDonnees(BaseReferentiel):
```

Dans `app/models/metier.py` :

```python
from app.models.base import BaseAudit
```

Puis, pour **chacune** des classes (`Utilisateur`, `Audit`, `Page`,
`AuditPage`, `AuditRegle`, `Constat`) : remplacer `(Base)` par `(BaseAudit)`.

- [ ] **Step 5: Restreindre la chaîne du référentiel à son domaine**

Dans `app/migration/env.py`, remplacer les lignes 18-23 par :

```python
# -- Import des modèles (nécessaire pour target_metadata) --------------------
# Seul le domaine du référentiel : les tables métier vivent dans une base
# distincte, avec sa propre chaîne (app/migration_audit/).
import app.models.etat  # noqa: E402, F401 — enregistre etat_donnees
import app.models.referentiel  # noqa: E402, F401 — enregistre les tables du référentiel
from app.models.base import BaseReferentiel  # noqa: E402

target_metadata = BaseReferentiel.metadata
```

- [ ] **Step 6: Lancer les tests et le lint**

Run: `uv run pytest tests/unit -v && uv run ruff check`
Expected: PASS. Aucun autre module n'importe `app.models.metier` — seul
`app/migration/env.py` le faisait.

- [ ] **Step 7: Vérifier que la base de développement est intacte**

Run:
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc \
  "SELECT count(*), count(*) FILTER (WHERE embedding IS NOT NULL) FROM regle;"
```
Expected: `245 | 245` — aucune migration n'a encore été jouée, rien n'a bougé.

- [ ] **Step 8: Commit**

```bash
git add app/models/ app/migration/env.py tests/unit/test_models_bases.py
git commit -m "refactor: split the declarative base per domain"
```

---

### Task 2 : `regle_numero` à la place de `regle_id`

**Files:**
- Modify: `app/models/metier.py:56-82`
- Test: `tests/unit/test_models_bases.py` (ajout)

**Interfaces:**
- Consumes: `BaseAudit` (Task 1).
- Produces: `AuditRegle.regle_numero` et `Constat.regle_numero`
  (`Integer`, `nullable=False`, sans `ForeignKey`). Clés primaires
  `(audit_id, regle_numero)` et `(audit_id, page_id, regle_numero)`. Les
  attributs `regle_id` n'existent plus.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à la fin de `tests/unit/test_models_bases.py` :

```python
def test_audit_regle_reference_le_numero_sans_fk():
    """La frontière entre bases interdit une FK : on référence la clé métier."""
    table = BaseAudit.metadata.tables["audit_regle"]

    assert "regle_numero" in table.c
    assert "regle_id" not in table.c
    assert [fk.target_fullname for fk in table.foreign_keys] == ["audit.id"]
    assert [colonne.name for colonne in table.primary_key] == [
        "audit_id",
        "regle_numero",
    ]


def test_constat_reference_le_numero_sans_fk():
    table = BaseAudit.metadata.tables["constat"]

    assert "regle_numero" in table.c
    assert "regle_id" not in table.c
    assert sorted(fk.target_fullname for fk in table.foreign_keys) == [
        "audit.id",
        "page.id",
    ]
    assert [colonne.name for colonne in table.primary_key] == [
        "audit_id",
        "page_id",
        "regle_numero",
    ]
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `uv run pytest tests/unit/test_models_bases.py -v -k numero`
Expected: FAIL — `KeyError: 'regle_numero'` ou `assert 'regle_id' not in ...`

- [ ] **Step 3: Modifier les deux modèles**

Dans `app/models/metier.py`, remplacer les classes `AuditRegle` et `Constat` :

```python
class AuditRegle(BaseAudit):
    __tablename__ = "audit_regle"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    # Clé métier Opquast, pas la clé de substitution du référentiel : une FK
    # ne traverse pas deux bases. Intégrité validée à la frontière API.
    regle_numero = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "regle_numero"),
    )


class Constat(BaseAudit):
    __tablename__ = "constat"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("page.id"), nullable=False)
    regle_numero = Column(Integer, nullable=False)
    statut = Column(String(32), nullable=False)
    commentaire = Column(String(512))
    recommandation = Column(String(512))
    preuve = Column(String(512))
    validation_humaine = Column(Boolean)
    feedback_auditeur = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "page_id", "regle_numero"),
    )
```

- [ ] **Step 4: Lancer les tests et le lint**

Run: `uv run pytest tests/unit -v && uv run ruff check`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/models/metier.py tests/unit/test_models_bases.py
git commit -m "refactor: reference rules by Opquast numero across the boundary"
```

---

### Task 3 : Création idempotente de la base d'audit

**Files:**
- Create: `scripts/create_db_audit.py`
- Modify: `Makefile` (nouvelle cible `create-db-audit`)
- Modify: `.env.example`

**Interfaces:**
- Consumes: rien.
- Produces: `scripts/create_db_audit.py`, exécutable via
  `uv run python scripts/create_db_audit.py`, qui crée la base nommée par
  `POSTGRES_DB_AUDIT` si elle est absente et sort en 0 dans les deux cas.
  Variables d'environnement attendues : `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB_AUDIT`.

- [ ] **Step 1: Ajouter les variables d'environnement**

Dans `.env.example`, à la suite des variables PostgreSQL existantes :

```dotenv
# Base du domaine audit (scission du 2026-09-08). La base nommée par
# POSTGRES_DB reste celle du référentiel Opquast.
POSTGRES_DB_AUDIT=qualicheck_audit
POSTGRES_TEST_DB_AUDIT=qualicheck_audit_test
```

Puis renseigner les deux mêmes variables dans le `.env` local (non versionné).

- [ ] **Step 2: Écrire le script**

Créer `scripts/create_db_audit.py` :

```python
"""Crée la base du domaine audit si elle n'existe pas déjà.

PostgreSQL n'a pas de CREATE DATABASE IF NOT EXISTS : on teste la présence
dans pg_database avant de créer. Idempotent, donc rejouable sans condition —
un seul mécanisme utilisé aussi bien en local qu'en CI, plutôt qu'un script
d'init Docker qui ne s'exécuterait que sur un volume vierge.

Le nom de la base vient de POSTGRES_DB_AUDIT ; le surcharger permet de créer
la base de test du même domaine.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.sql import SQL, Identifier

load_dotenv()


def main() -> None:
    nom = os.environ["POSTGRES_DB_AUDIT"]

    # CREATE DATABASE ne peut pas tourner dans une transaction : on se
    # connecte à la base d'administration en autocommit.
    connexion = psycopg2.connect(
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname="postgres",
    )
    connexion.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (nom,))
            if curseur.fetchone():
                print(f"Base « {nom} » déjà présente, rien à faire.")
                return

            # Identifier() échappe le nom, qui vient de l'environnement.
            curseur.execute(SQL("CREATE DATABASE {}").format(Identifier(nom)))
            print(f"Base « {nom} » créée.")
    finally:
        connexion.close()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Ajouter la cible Makefile**

Dans `Makefile`, juste avant la cible `migration:` :

```makefile
## Crée la base du domaine audit si elle est absente (idempotent)
create-db-audit:
	uv run python scripts/create_db_audit.py
```

- [ ] **Step 4: Vérifier l'idempotence par l'exécution**

Run: `make create-db-audit && make create-db-audit`
Expected: premier appel « Base « qualicheck_audit » créée. », second appel
« Base « qualicheck_audit » déjà présente, rien à faire. » — code de sortie 0
les deux fois.

- [ ] **Step 5: Vérifier que les deux bases coexistent**

Run: `docker exec qualicheck-postgres psql -U qualicheck -d postgres -c "\l" | grep qualicheck`
Expected: `qualicheck` et `qualicheck_audit` tous les deux listés.

- [ ] **Step 6: Lint et commit**

```bash
uv run ruff check
git add scripts/create_db_audit.py Makefile .env.example
git commit -m "feat: add idempotent creation of the audit database"
```

---

### Task 4 : Chaîne Alembic du domaine audit

**Files:**
- Create: `app/migration_audit/alembic.ini`
- Create: `app/migration_audit/env.py`
- Create: `app/migration_audit/versions/0001_schema_audit.py`
- Modify: `scripts/migration.py`
- Modify: `Makefile`
- Test: `tests/migration/test_migration_audit.py`

**Interfaces:**
- Consumes: `BaseAudit` avec `regle_numero` (Tasks 1-2), la base créée
  (Task 3).
- Produces: `scripts/migration.py` accepte un argument de domaine
  (`referentiel` par défaut, ou `audit`) ; `make migration-audit` et
  `make migration-audit-test`. La révision `0001` de la chaîne audit crée les
  six tables.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/migration/test_migration_audit.py` :

```python
"""
Vérifie le schéma réellement en place dans la base du domaine audit.

Lecture seule sur la base de développement du domaine (même exception
assumée que tests/migration/test_migration.py pour le référentiel).
Nécessite : make create-db-audit && make migration-audit.
"""

import os

import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()

TABLES_ATTENDUES = [
    "utilisateur",
    "audit",
    "page",
    "audit_page",
    "audit_regle",
    "constat",
]


@pytest.fixture
def conn():
    connexion = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB_AUDIT"],
    )
    yield connexion
    connexion.close()


def test_toutes_les_tables_du_domaine_existent(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = {ligne[0] for ligne in curseur.fetchall()}

    manquantes = set(TABLES_ATTENDUES) - tables
    assert not manquantes, f"Tables absentes : {manquantes}"


def test_le_referentiel_est_absent_de_cette_base(conn):
    """Preuve d'isolation : la table regle n'est pas joignable depuis ici."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT to_regclass('public.regle') IS NULL, to_regclass('public.theme') IS NULL;"
        )
        regle_absente, theme_absent = curseur.fetchone()

    assert regle_absente, "La table regle ne doit pas exister dans la base d'audit"
    assert theme_absent, "La table theme ne doit pas exister dans la base d'audit"


def test_aucune_fk_ne_sort_du_domaine(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT conrelid::regclass::text, confrelid::regclass::text
            FROM pg_constraint
            WHERE contype = 'f';
            """
        )
        liens = curseur.fetchall()

    cibles_hors_domaine = {
        cible for _, cible in liens if cible not in TABLES_ATTENDUES
    }
    assert not cibles_hors_domaine, f"FK vers l'extérieur : {cibles_hors_domaine}"


def test_pk_composite_audit_regle(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT string_agg(a.attname, ',' ORDER BY k.ord)
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.conrelid = 'audit_regle'::regclass AND c.contype = 'p';
            """
        )
        assert curseur.fetchone()[0] == "audit_id,regle_numero"


def test_pk_composite_constat(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT string_agg(a.attname, ',' ORDER BY k.ord)
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.conrelid = 'constat'::regclass AND c.contype = 'p';
            """
        )
        assert curseur.fetchone()[0] == "audit_id,page_id,regle_numero"


def test_index_btree_constat_audit_id(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_constat_audit_id';"
        )
        assert curseur.fetchone()[0] == 1


def test_index_btree_audit_regle_audit_id(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_audit_regle_audit_id';"
        )
        assert curseur.fetchone()[0] == 1


def test_colonnes_not_null_audit(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'audit'
              AND column_name IN ('utilisateur_id', 'url_depart', 'statut', 'date_creation')
              AND is_nullable = 'YES';
            """
        )
        nullable = [ligne[0] for ligne in curseur.fetchall()]

    assert not nullable, f"Colonnes audit incorrectement nullable : {nullable}"
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `uv run pytest tests/migration/test_migration_audit.py -v`
Expected: FAIL — les tables n'existent pas encore (`Tables absentes : {...}`).

- [ ] **Step 3: Créer la configuration Alembic du domaine**

Créer `app/migration_audit/alembic.ini` — copie de
`app/migration/alembic.ini`, identique (le `script_location = .` reste
valide puisque le fichier vit dans son propre dossier).

Créer `app/migration_audit/env.py` :

```python
import os
import sys
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# -- Résolution des chemins --------------------------------------------------
# env.py est exécuté par Alembic depuis app/migration_audit/.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# -- Chargement du .env ------------------------------------------------------
load_dotenv(ROOT / ".env")

# -- Import des modèles (nécessaire pour target_metadata) --------------------
# Seul le domaine audit : le référentiel vit dans une base distincte, avec sa
# propre chaîne (app/migration/).
import app.models.metier  # noqa: E402, F401 — enregistre les tables métier
from app.models.base import BaseAudit  # noqa: E402

target_metadata = BaseAudit.metadata


# -- Construction de l'URL de connexion --------------------------------------
def get_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB_AUDIT"]
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

- [ ] **Step 4: Écrire la migration initiale du domaine**

Créer `app/migration_audit/versions/0001_schema_audit.py` :

```python
"""Schéma initial du domaine audit

Reprend les six tables métier telles qu'elles existaient dans la base du
référentiel, à une différence près : les liens vers regle passent par le
numero Opquast, sans clé étrangère — une FK ne traverse pas deux bases.
Décision : jury/decisions/2026-09-08-deux-bases-referentiel-audit.md

Revision ID: 0001
Revises:
Create Date: 2026-09-08
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utilisateur_id", sa.Integer(), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime(), nullable=False),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "page",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("statut_http", sa.String(10), nullable=True),
        sa.Column("est_selectionnee", sa.Boolean(), nullable=False),
        sa.Column("date_crawl", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )

    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("regle_numero", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.PrimaryKeyConstraint("audit_id", "regle_numero"),
    )
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])

    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("regle_numero", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512), nullable=True),
        sa.Column("recommandation", sa.String(512), nullable=True),
        sa.Column("preuve", sa.String(512), nullable=True),
        sa.Column("validation_humaine", sa.Boolean(), nullable=True),
        sa.Column("feedback_auditeur", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_numero"),
    )
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])


def downgrade() -> None:
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.drop_table("constat")
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")
```

- [ ] **Step 5: Rendre le point d'entrée conscient du domaine**

`scripts/migration.py`, contenu complet :

```python
"""Point d'entrée pour appliquer les migrations Alembic.

Deux domaines, deux chaînes, deux bases (scission du 2026-09-08) :
    python scripts/migration.py             -> référentiel (défaut)
    python scripts/migration.py audit       -> domaine audit

Lance `alembic upgrade head` depuis le dossier de la chaîne visée et retourne
le code de sortie d'Alembic (0 = succès, non-nul = erreur).
"""
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "app"

# Nom du domaine -> dossier contenant son alembic.ini
CHAINES = {
    "referentiel": RACINE / "migration",
    "audit": RACINE / "migration_audit",
}


def main() -> None:
    domaine = sys.argv[1] if len(sys.argv) > 1 else "referentiel"
    if domaine not in CHAINES:
        attendus = ", ".join(sorted(CHAINES))
        print(f"Domaine inconnu : {domaine!r}. Attendu : {attendus}.")
        sys.exit(2)

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=CHAINES[domaine],
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Ajouter les cibles Makefile**

Après la cible `migration-test:` existante :

```makefile
## Migre la base du domaine audit (la crée si absente)
migration-audit: create-db-audit
	uv run python scripts/migration.py audit

## Crée (si absente) et migre la base de test du domaine audit
migration-audit-test:
	POSTGRES_DB_AUDIT="$$(grep POSTGRES_TEST_DB_AUDIT .env | cut -d= -f2)" \
		uv run python scripts/create_db_audit.py
	POSTGRES_DB_AUDIT="$$(grep POSTGRES_TEST_DB_AUDIT .env | cut -d= -f2)" \
		uv run python scripts/migration.py audit
```

- [ ] **Step 7: Appliquer et vérifier**

Run: `make migration-audit && uv run pytest tests/migration/test_migration_audit.py -v`
Expected: PASS — 8 tests, dont la preuve d'isolation
(`test_le_referentiel_est_absent_de_cette_base`).

- [ ] **Step 8: Vérifier la réversibilité**

Run:
```bash
cd app/migration_audit && uv run alembic downgrade base && uv run alembic upgrade head && cd -
uv run pytest tests/migration/test_migration_audit.py -v
```
Expected: PASS après le cycle complet.

- [ ] **Step 9: Vérifier que le référentiel est intact**

Run:
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc \
  "SELECT count(*), count(*) FILTER (WHERE embedding IS NOT NULL) FROM regle;"
```
Expected: `245 | 245`

- [ ] **Step 10: Lint et commit**

```bash
uv run ruff check
git add app/migration_audit/ scripts/migration.py Makefile tests/migration/test_migration_audit.py
git commit -m "feat: add the audit domain migration chain"
```

---

### Task 5 : Retirer les tables métier de la base du référentiel

**Files:**
- Create: `app/migration/versions/0013_drop_tables_metier.py`
- Modify: `tests/migration/test_migration.py`

**Interfaces:**
- Consumes: la chaîne audit opérationnelle (Task 4) — les tables existent
  désormais ailleurs avant d'être retirées ici.
- Produces: base du référentiel sans aucune table métier ;
  `tests/migration/test_migration.py` n'assertant plus que le référentiel.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `tests/migration/test_migration.py`, retirer les six tables métier de
`TABLES_ATTENDUES` (ligne 45-49) pour ne garder que le référentiel :

```python
TABLES_ATTENDUES = [
    "theme", "regle", "objectif", "phase", "tag",
    "objectif_regle", "phase_regle", "regle_tag",
    "etat_donnees",
]
```

Supprimer les cinq tests devenus étrangers à ce domaine :
`test_index_btree_constat_audit_id`, `test_index_btree_audit_regle_audit_id`,
`test_colonnes_not_null_audit`, `test_pk_composite_constat` et
`test_pk_composite_audit_page` — ils vivent désormais dans
`test_migration_audit.py` (Task 4), où `test_pk_composite_constat` attend
`audit_id,page_id,regle_numero`.

Ajouter à la place la preuve d'isolation symétrique :

```python
TABLES_DU_DOMAINE_AUDIT = [
    "utilisateur", "audit", "page", "audit_page", "audit_regle", "constat",
]


def test_le_domaine_audit_est_absent_de_cette_base(conn):
    """Preuve d'isolation : les tables métier ont quitté le référentiel."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = {ligne[0] for ligne in curseur.fetchall()}

    restantes = set(TABLES_DU_DOMAINE_AUDIT) & tables
    assert not restantes, f"Tables métier encore présentes : {restantes}"


def test_les_245_regles_sont_intactes(conn):
    """Garde-fou : aucune migration de ce chantier ne touche aux données."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*), count(*) FILTER (WHERE embedding IS NOT NULL) FROM regle;"
        )
        total, vectorisees = curseur.fetchone()

    assert total == 245
    assert vectorisees == 245
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `uv run pytest tests/migration/test_migration.py -v -k domaine_audit`
Expected: FAIL — `Tables métier encore présentes : {'audit', 'page', ...}`

- [ ] **Step 3: Écrire la migration**

Créer `app/migration/versions/0013_drop_tables_metier.py` :

```python
"""Retire les six tables métier de la base du référentiel

Elles vivent désormais dans qualicheck_audit, sous leur forme cible
(regle_numero au lieu de regle_id) — voir app/migration_audit/versions/.
Aucune donnée à déplacer : les six tables étaient vides (vérifié le
2026-09-08). Décision et trace du schéma d'avant :
jury/decisions/2026-09-08-deux-bases-referentiel-audit.md

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-08
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ordre inverse des dépendances.
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.drop_table("constat")
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")


def downgrade() -> None:
    """Recrée les six tables sous leur forme d'ORIGINE.

    C'est bien la réciproque de cette migration — donc avec regle_id et les
    deux clés étrangères vers regle — et non la forme cible du domaine audit.
    """
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utilisateur_id", sa.Integer(), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime(), nullable=False),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "page",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("statut_http", sa.String(10), nullable=True),
        sa.Column("est_selectionnee", sa.Boolean(), nullable=False),
        sa.Column("date_crawl", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )
    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("regle_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["regle_id"], ["regle.id"]),
        sa.PrimaryKeyConstraint("audit_id", "regle_id"),
    )
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])
    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("regle_id", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512), nullable=True),
        sa.Column("recommandation", sa.String(512), nullable=True),
        sa.Column("preuve", sa.String(512), nullable=True),
        sa.Column("validation_humaine", sa.Boolean(), nullable=True),
        sa.Column("feedback_auditeur", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.ForeignKeyConstraint(["regle_id"], ["regle.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])
```

- [ ] **Step 4: Appliquer et vérifier**

Run: `make migration && uv run pytest tests/migration/test_migration.py -v`
Expected: PASS, y compris `test_le_domaine_audit_est_absent_de_cette_base` et
`test_les_245_regles_sont_intactes`.

- [ ] **Step 5: Vérifier la réversibilité sans perdre de données**

Run:
```bash
cd app/migration && uv run alembic downgrade 0012 && cd -
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc \
  "SELECT count(*) FROM regle;"
cd app/migration && uv run alembic upgrade head && cd -
uv run pytest tests/migration/test_migration.py -v
```
Expected: `245` après le downgrade, PASS après le retour à `head`.

- [ ] **Step 6: Prouver l'isolation dans les deux sens**

Run:
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck_audit \
  -c "SELECT count(*) FROM regle;"
```
Expected: ERREUR `relation "regle" does not exist` — c'est le résultat
attendu, et c'est tout l'intérêt du chantier.

- [ ] **Step 7: Commit**

```bash
git add app/migration/versions/0013_drop_tables_metier.py tests/migration/test_migration.py
git commit -m "feat: drop business tables from the referential database"
```

---

### Task 6 : Deux moteurs de connexion

**Files:**
- Modify: `app/db.py`
- Test: `tests/unit/test_db.py`

**Interfaces:**
- Consumes: `POSTGRES_DB` et `POSTGRES_DB_AUDIT` (Task 3).
- Produces: `build_database_url_referentiel()`,
  `build_database_url_audit()`, `get_session_referentiel()`,
  `get_session_audit()`. **`build_database_url()` et `get_session()`
  disparaissent** — `app/api_regles/regles.py` et
  `tests/integration/api_regles/test_regles.py` référencent `get_session` et
  doivent être mis à jour dans cette tâche.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à `tests/unit/test_db.py` :

```python
def test_les_deux_url_visent_deux_bases_distinctes(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("POSTGRES_HOST", "h")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "referentiel_x")
    monkeypatch.setenv("POSTGRES_DB_AUDIT", "audit_x")

    from app.db import build_database_url_audit, build_database_url_referentiel

    assert build_database_url_referentiel().endswith("/referentiel_x")
    assert build_database_url_audit().endswith("/audit_x")
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `uv run pytest tests/unit/test_db.py -v -k deux_url`
Expected: FAIL — `ImportError: cannot import name 'build_database_url_audit'`

- [ ] **Step 3: Réécrire `app/db.py`**

Remplacer le contenu à partir de `def build_database_url()` par :

```python
def _build_url(nom_base: str) -> str:
    """URL de connexion à la base nommée, depuis les identifiants du .env."""
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{nom_base}"


def build_database_url_referentiel() -> str:
    """Base du référentiel Opquast (245 règles, vecteurs)."""
    return _build_url(os.environ["POSTGRES_DB"])


def build_database_url_audit() -> str:
    """Base du domaine audit."""
    return _build_url(os.environ["POSTGRES_DB_AUDIT"])


# Un moteur par base pour tout le processus : un pool recréé à chaque requête
# annulerait l'intérêt du pool. Aucune session « par défaut » n'est exposée —
# tout appelant doit dire quel domaine il interroge.
_engine_referentiel = create_engine(build_database_url_referentiel())
_SessionReferentiel = sessionmaker(bind=_engine_referentiel)


def get_session_referentiel() -> Iterator[Session]:
    """Dépendance FastAPI : une session référentiel par requête."""
    session = _SessionReferentiel()
    try:
        yield session
    finally:
        session.close()


def get_session_audit() -> Iterator[Session]:
    """Dépendance FastAPI : une session audit par requête.

    Le moteur est construit à l'appel et non au chargement du module : aucun
    service ne consomme encore ce domaine (app/api_audit reste à concevoir
    avec US1), inutile d'exiger POSTGRES_DB_AUDIT de tous les points d'entrée.
    """
    engine = create_engine(build_database_url_audit())
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
```

Supprimer `build_engine()`, `build_database_url()` et `get_session()`.

- [ ] **Step 4: Mettre à jour les deux appelants**

Dans `app/api_regles/regles.py`, remplacer les trois usages de `get_session` :

```python
from app.db import get_session_referentiel
```

puis, dans chacune des trois routes,
`session: Session = Depends(get_session_referentiel)`.

Dans `tests/integration/api_regles/test_regles.py` :

```python
from app.db import get_session_referentiel
```

et dans la fixture `client` :
`app.dependency_overrides[get_session_referentiel] = lambda: session`.

- [ ] **Step 5: Lancer les tests**

Run: `uv run pytest tests/unit tests/integration -v && uv run ruff check`
Expected: PASS. Vérifier au passage qu'aucun `get_session` orphelin ne
subsiste : `grep -rn "get_session\b" app/ tests/ scripts/` ne doit rien
retourner.

- [ ] **Step 6: Commit**

```bash
git add app/db.py app/api_regles/regles.py tests/unit/test_db.py tests/integration/api_regles/test_regles.py
git commit -m "refactor: expose one named engine per database"
```

---

### Task 7 : Sauvegardes bornées au référentiel

**Files:**
- Modify: `Makefile` (cibles `export_sql` et `import_sql`)

**Interfaces:**
- Consumes: rien.
- Produces: `make export_sql` produit un dump ne contenant que le
  référentiel.

- [ ] **Step 1: Documenter le périmètre des deux cibles**

**Aucune commande ne change.** `POSTGRES_DB` désignant désormais la seule
base du référentiel, le dump ne peut plus contenir de table métier : la
correction est acquise par la scission elle-même. Ce qui manque est la
mention du périmètre, pour qu'un lecteur ne croie pas sauvegarder tout le
projet.

Dans `Makefile`, remplacer la ligne de commentaire qui précède `export_sql:`
par :

```makefile
## Exporte les données du RÉFÉRENTIEL uniquement — le domaine audit a sa
## propre base et n'est pas couvert ici. Avant la scission du 2026-09-08,
## cette cible dumpait toute la base : « sauvegarder le référentiel »
## sauvegardait aussi les audits, et une restauration les ramenait en
## arrière. Voir jury/decisions/2026-09-08-deux-bases-referentiel-audit.md
```

Et de même avant `import_sql:` :

```makefile
## Importe un dump de RÉFÉRENTIEL généré par make export_sql. Ne vide rien
## avant restauration : si des lignes existent déjà, les conflits de clé
## primaire remontent. Ne concerne pas le domaine audit.
```

- [ ] **Step 2: Vérifier par le contenu du dump**

Run:
```bash
make export_sql
grep -cE "COPY public\.(audit|constat|page|utilisateur|audit_page|audit_regle) " backups/*.sql | tail -1
```
Expected: `0` — aucune table métier dans le dump.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "docs: scope the SQL backup targets to the referential"
```

---

### Task 8 : CI

**Files:**
- Modify: `.gitea/workflows/ci-dev.yml`

**Interfaces:**
- Consumes: `scripts/create_db_audit.py` (Task 3),
  `scripts/migration.py audit` (Task 4).
- Produces: un run CI qui crée et migre les deux bases avant les tests.

- [ ] **Step 1: Déclarer la base d'audit et la migrer**

Dans `.gitea/workflows/ci-dev.yml`, ajouter au bloc `env:` (après la ligne
`POSTGRES_TEST_DB`) :

```yaml
      # Le nom d'une base n'est pas un secret, et celle du service CI est
      # éphémère : littéral plutôt qu'un secret supplémentaire à gérer.
      POSTGRES_DB_AUDIT: qualicheck_audit
      POSTGRES_TEST_DB_AUDIT: qualicheck_audit
```

Puis remplacer l'étape « Appliquer les migrations » par :

```yaml
      - name: Appliquer les migrations du référentiel
        run: uv run python scripts/migration.py

      - name: Créer et migrer la base du domaine audit
        run: |
          uv run python scripts/create_db_audit.py
          uv run python scripts/migration.py audit
```

- [ ] **Step 2: Vérifier que le staging n'a besoin de rien**

La spec (§4.9) annonçait une modification de `cd-staging.yml` et un secret
`POSTGRES_DB_AUDIT` de plus. **Ce n'est pas nécessaire** : le staging ne
déploie qu'`api_regles`, qui ne touche que le référentiel, et
`get_session_audit()` construit son moteur à l'appel (Task 6) — donc rien ne
lit `POSTGRES_DB_AUDIT` au démarrage. Le staging aura besoin de la base
d'audit le jour où `api_audit` existera, pas avant.

À prouver, plutôt qu'à supposer :

```bash
env -u POSTGRES_DB_AUDIT -u POSTGRES_TEST_DB_AUDIT \
  uv run python -c "from app.api_regles.main import app; print('démarrage OK')"
```
Expected: `démarrage OK` — l'API se charge sans la variable.

Si cette vérification échoue, c'est que `get_session_audit` est évalué au
chargement : corriger Task 6 plutôt que d'ajouter un secret au staging.

- [ ] **Step 3: Pousser et observer un run réel**

Run: `git push gitea dev` puis `tea actions runs --repo david/qualicheck --login qualicheck`
Expected: run vert. La CI n'exécute que `tests/unit` et `tests/integration`,
donc `tests/migration/` n'y tourne pas — c'est l'état existant, inchangé.

- [ ] **Step 4: Commit**

```bash
git add .gitea/workflows/ci-dev.yml
git commit -m "ci: create and migrate the audit database"
```

---

### Task 9 : Documents de conception durables et contrôle anti-dérive

**Files:**
- Modify: `conception/1_BDD/bdd.md`
- Modify: `conception/1_BDD/MLD_qualicheck.md`
- Modify: `docs/rgpd/registre_traitements.md`
- Modify: `CHANGELOG.md`, `TODO.md`

**Interfaces:**
- Consumes: l'état final des tâches 1 à 8.
- Produces: aucune interface de code — la source de vérité désignée par
  `docs/README.md` décrit deux bases.

- [ ] **Step 1: Corriger `conception/1_BDD/bdd.md`**

Trois affirmations à réécrire :
- § Contexte et objectif, ligne 18 : « ce document couvre **l'intégralité du
  schéma** » — remplacer par la répartition en deux bases, avec renvoi à
  `jury/decisions/2026-09-08-deux-bases-referentiel-audit.md`.
- § Choix technique, ligne 30 : « La première migration crée le schéma
  complet » — devient deux chaînes, une par domaine.
- § Déclenchement, ligne 44-48 : l'ordre d'exécution mentionne un seul
  `scripts/migration.py` — préciser `migration.py` (référentiel) puis
  `migration.py audit`, et `make create-db-audit` en préalable.

- [ ] **Step 2: Corriger `conception/1_BDD/MLD_qualicheck.md`**

- Indiquer la base d'accueil de chaque table (deux sections, ou une colonne).
- § Cardinalités du MCD : les deux relations `regle — audit_regle` et
  `regle — constat` ne sont plus des relations d'un même modèle ; les
  remplacer par une mention explicite de la frontière et du `regle_numero`.
- Remplacer `regle_id` par `regle_numero` dans les blocs `audit_regle` et
  `constat`, et corriger leurs clés primaires.

- [ ] **Step 3: Corriger `docs/rgpd/registre_traitements.md`**

Le périmètre des données personnelles devient une base
(`qualicheck_audit`) : le dire explicitement, c'est l'un des quatre critères
qui motivent la décision.

- [ ] **Step 4: Contrôle anti-dérive**

Run:
```bash
grep -rn "une seule base\|schéma complet\|regle_id" conception/ docs/rgpd/ docs/README.md
```
Expected: aucune occurrence décrivant le présent. Les mentions historiques
(dans une trace datée, un document d'incident ou le `downgrade` d'une
migration) sont légitimes et doivent rester.

- [ ] **Step 5: Tracer et committer**

Ajouter l'entrée `CHANGELOG.md` couvrant les neuf tâches, cocher l'entrée de
`TODO.md` § Prochain gros morceau, puis :

```bash
git add conception/ docs/rgpd/ CHANGELOG.md TODO.md
git commit -m "docs: align design documents with the two-database split"
```

---

## Ce que ce plan ne fait pas

- **`GET /dense`** — désigné par la décision, construit avec US2.
- **`app/api_audit`** — service à concevoir avec la spec US1. Ce plan crée sa
  base et son schéma, pas son service.
- **Validation applicative du `regle_numero`** — appartient à `api_audit`.
- **Sauvegarde du domaine audit** — aucune donnée à sauvegarder aujourd'hui.
- **Renommage de `qualicheck` en `qualicheck_referentiel`** — dette assumée,
  documentée dans la décision.
- **Le MCD (`B_MCD_qualicheck.drawio`)** — à traiter en un seul passage avec
  les deux points de notation déjà ouverts dans `TODO.md` (association
  ternaire de `constat`, colonnes absentes), plutôt que d'y revenir trois
  fois.
