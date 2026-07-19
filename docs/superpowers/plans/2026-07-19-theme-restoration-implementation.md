# Theme Restoration + Tags Optional Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the `theme` table and `regle.theme_id` FK (erroneously removed in a prior commit) and make `tags` optional, based on empirical inspection of the real Opquast API data — `metadata.Thématiques` is always present with exactly one value (245/245 rules) while `metadata.Tags` is empty on 64/245 rules.

**Architecture:** `theme` is a simple 1-N relation (unlike `tag`/`phase`/`objectif` which are many-to-many) — a plain FK column on `regle`, no association table. The change threads through the whole pipeline: Pydantic models → acquisition mapping → migration/ORM models → storage upsert, plus every test fixture that constructs a `Rule`/`RuleAggregation`/`EnrichedRule`.

**Tech Stack:** Pydantic v2 (`field_validator`), Alembic (migration 0001, modified in place — never merged to `main`), SQLAlchemy 2.x ORM, pytest.

## Global Constraints

- **Field name:** `theme` (not `thematique`) — single consistent term across API mapping, Pydantic, and SQL, even though the API key is `metadata.Thématiques`
- **Field type:** `theme: str` on `RuleAcquisition`/`RuleAggregation` — extracted as `metadata["Thématiques"][0]` at acquisition time, never a `list[str]` (cardinality is always exactly 1, confirmed empirically)
- **theme validation:** non-empty string, grouped with `intitule`/`solution`/`controle` in `RuleAggregation`'s `non_empty_string` validator
- **tags validation:** removed from `non_empty_list` — empty list is now valid, no validator applies to `tags` anymore
- **objectifs/phases:** unchanged — still validated non-empty via `non_empty_list`
- **DB relation:** `theme` table (`id`, `theme` VARCHAR(64) NOT NULL UNIQUE) + `regle.theme_id` (FK NOT NULL) — no association table, no `ThemeRegle` class
- **Migration:** modify `0001_schema_initial.py` directly (never merged to `main`), not a new migration file
- **Code:** English (class/function/variable names) — `Theme`, `theme_id`
- **Docs/comments/logs:** French
- **Docs already corrected:** `conception/` files were updated in a prior commit (`docs: restore theme table in MCD/MLD...`) — no conception doc changes needed in this plan
- **No new .drawio edits:** they already contain `theme` correctly (never touched during the erroneous removal)
- **Existing DB rows:** the 3 validation rules (numero 1, 3, 4) stored without `theme_id` will be wiped by the downgrade/migration cycle in this plan — acceptable per spec, no data migration needed

---

## Task 1: Add `theme` to Pydantic models, make `tags` optional

**Files:**
- Modify: `app/ingestion/schema.py`
- Test: `tests/unit/ingestion/test_aggregation.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `RuleAcquisition.theme: str`, `RuleAggregation.theme: str` (validated non-empty), `EnrichedRule.theme: str` (inherited, no change needed). `RuleAggregation` no longer validates `tags` for non-emptiness.

- [ ] **Step 1: Write failing test for theme field acceptance and tags-empty acceptance**

Replace the entire content of `tests/unit/ingestion/test_aggregation.py`:

```python
"""
Tests unitaires pour app/ingestion/aggregation.py

Teste la fusion de données acquises (API + scraping) en objets Rule validés,
et la composition d'une collection Rules complètement validée.
"""

from app.ingestion.aggregation import Rule, Rules, aggregate_rules


class TestRule:
    """Tests de la classe Rule (modèle de domaine)."""

    def test_regle_creation_with_all_fields(self):
        """Crée une Rule avec tous les champs requis."""
        regle = Rule(
            id=1,
            number=1,
            intitule="Titule de la règle",
            theme="Contenus",
            solution="Mettre en place X",
            controle="Vérifier Y",
            objectifs=["Accessibilité"],
            tags=["HTML"],
            phases=["Intégration"],
            slug="regle-avec-des-tirets",
        )

        assert regle.id == 1
        assert regle.number == 1
        assert regle.intitule == "Titule de la règle"
        assert regle.theme == "Contenus"
        assert regle.solution == "Mettre en place X"
        assert regle.controle == "Vérifier Y"
        assert regle.objectifs == ["Accessibilité"]
        assert regle.tags == ["HTML"]
        assert regle.phases == ["Intégration"]
        assert regle.slug == "regle-avec-des-tirets"

    def test_regle_creation_with_empty_tags(self):
        """Crée une Rule avec une liste tags vide (désormais accepté)."""
        regle = Rule(
            id=1,
            number=1,
            intitule="Intitulé",
            theme="Contenus",
            solution="Solution",
            controle="Contrôle",
            objectifs=["Objectif"],
            tags=[],
            phases=["Phase"],
            slug="slug",
        )

        assert regle.tags == []

    def test_regle_fails_if_intitule_empty(self):
        """Lève une erreur si intitulé vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="",
                theme="Contenus",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_theme_empty(self):
        """Lève une erreur si theme vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                theme="",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_solution_empty(self):
        """Lève une erreur si solution vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                theme="Contenus",
                solution="",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_controle_empty(self):
        """Lève une erreur si contrôle vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                theme="Contenus",
                solution="Solution",
                controle="",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_objectifs_empty(self):
        """Lève une erreur si liste d'objectifs vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                theme="Contenus",
                solution="Solution",
                controle="Contrôle",
                objectifs=[],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_phases_empty(self):
        """Lève une erreur si liste de phases vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                theme="Contenus",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=[],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass


class TestRules:
    """Tests de la classe Rules (collection)."""

    def test_regles_creation_from_regle_list(self):
        """Crée une collection Rules à partir d'une liste de Regle."""
        regle1 = Rule(
            id=1,
            number=1,
            intitule="Règle 1",
            theme="Contenus",
            solution="Solution 1",
            controle="Contrôle 1",
            objectifs=["Objectif 1"],
            tags=["Tag 1"],
            phases=["Phase 1"],
            slug="regle-1",
        )
        regle2 = Rule(
            id=2,
            number=2,
            intitule="Règle 2",
            theme="Navigation",
            solution="Solution 2",
            controle="Contrôle 2",
            objectifs=["Objectif 2"],
            tags=["Tag 2"],
            phases=["Phase 2"],
            slug="regle-2",
        )

        regles = Rules([regle1, regle2])

        assert len(regles.regles) == 2
        assert regles.regles[0].number == 1
        assert regles.regles[1].number == 2

    def test_regles_fails_if_empty_list(self):
        """Lève une erreur si collection vide."""
        try:
            Rules([])
            assert False, "Should have raised an error"
        except ValueError:
            pass


class TestAggregateRules:
    """Tests de la fonction aggregate_rules."""

    def test_aggregate_rules_from_acquisition_output(self):
        """Agrège des règles acquises (dicts API + scraping) en Rules validé."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                "theme": "Contenus",
                "solution": "Solution 1",
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            },
            {
                "id": 2,
                "number": 2,
                "intitule": "Règle 2",
                "theme": "Navigation",
                "solution": "Solution 2",
                "controle": "Contrôle 2",
                "objectifs": ["Performance"],
                "tags": [],
                "phases": ["Design"],
                "slug": "regle-2",
            },
        ]

        regles = aggregate_rules(acquired_rules)

        assert isinstance(regles, Rules)
        assert len(regles.regles) == 2
        assert regles.regles[0].number == 1
        assert regles.regles[0].intitule == "Règle 1"
        assert regles.regles[0].theme == "Contenus"
        assert regles.regles[1].number == 2
        assert regles.regles[1].tags == []

    def test_aggregate_rules_fails_if_missing_intitule(self):
        """Lève une erreur si champ 'intitule' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                # intitule manquant
                "theme": "Contenus",
                "solution": "Solution 1",
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass

    def test_aggregate_rules_fails_if_missing_theme(self):
        """Lève une erreur si champ 'theme' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                # theme manquant
                "solution": "Solution 1",
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass

    def test_aggregate_rules_fails_if_missing_solution(self):
        """Lève une erreur si champ 'solution' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                "theme": "Contenus",
                # solution manquante
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass

    def test_aggregate_rules_fails_if_missing_controle(self):
        """Lève une erreur si champ 'controle' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                "theme": "Contenus",
                "solution": "Solution 1",
                # controle manquant
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_aggregation.py -v
```

Expected: FAIL — `theme` is an unexpected keyword argument for `Rule` (Pydantic rejects unknown fields), since `RuleAggregation` doesn't have a `theme` field yet.

- [ ] **Step 3: Add theme field and update validators in schema.py**

Modify `app/ingestion/schema.py` — replace the full file content:

```python
"""
Schémas Pydantic pour le pipeline d'ingestion.

Détail : conception/2_ingestion/ingestion.md
"""

from pydantic import BaseModel, Field, field_validator


class RuleAcquisition(BaseModel):
    """Données brutes acquises pour une règle (API + scraping)."""

    id: int
    number: int
    intitule: str
    theme: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    slug: str
    solution: str | None = Field(default=None)
    controle: str | None = Field(default=None)


class RuleAggregation(BaseModel):
    """Règle complètement validée après agrégation (données requises non-vides)."""

    id: int
    number: int
    intitule: str
    theme: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    slug: str
    solution: str
    controle: str

    @field_validator("objectifs", "phases")
    @classmethod
    def non_empty_list(cls, v):
        if not v:
            raise ValueError("La liste ne peut pas être vide")
        return v

    @field_validator("intitule", "theme", "solution", "controle")
    @classmethod
    def non_empty_string(cls, v):
        if not v or not v.strip():
            raise ValueError("La chaîne ne peut pas être vide")
        return v


class EnrichedRule(RuleAggregation):
    """Règle complètement enrichie par l'agent LLM."""

    strategie_analyse: str
    strategie_justification: str
    guide_analyse: str
    strategie_source: str = "ia_import"
    llm_provider: str = "kimi-k2.6"

    @field_validator("strategie_analyse", "strategie_justification", "guide_analyse")
    @classmethod
    def non_empty_enrichment_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("La chaîne ne peut pas être vide")
        return v
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_aggregation.py -v
```

Expected: All tests PASS (15 tests: original set minus `test_regle_fails_if_tags_empty`, plus `test_regle_creation_with_empty_tags`, `test_regle_fails_if_theme_empty`, `test_aggregate_rules_fails_if_missing_theme`).

- [ ] **Step 5: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/schema.py tests/unit/ingestion/test_aggregation.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/schema.py tests/unit/ingestion/test_aggregation.py && git commit -m "feat: add theme field to Pydantic models, make tags optional

- RuleAcquisition/RuleAggregation gain theme: str (extracted as scalar,
  not list — API always returns exactly 1 Thématiques value per rule)
- theme validated non-empty, grouped with intitule/solution/controle
- tags removed from non_empty_list validator — empty list now valid,
  no validator applies to tags anymore (64/245 real rules have no tags)
- objectifs/phases unchanged, still required non-empty

Tests: theme creation + validation, tags-empty acceptance, updated all
existing fixtures with theme=...

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Map `theme` in acquisition.py

**Files:**
- Modify: `app/ingestion/acquisition.py`
- Test: `tests/unit/ingestion/test_acquisition.py`

**Interfaces:**
- Consumes: `RuleAcquisition` (from Task 1, now requires `theme`)
- Produces: `fetch_api()` output dicts now include a `"theme"` key

- [ ] **Step 1: Write failing test for theme mapping**

Modify `tests/unit/ingestion/test_acquisition.py` — replace the `TestFetchApi` class:

```python
class TestFetchApi:
    """Tests de la fonction fetch_api."""

    @patch("app.ingestion.acquisition.requests.get")
    def test_fetch_api_returns_list(self, mock_get):
        """Vérifie que fetch_api retourne une liste de règles avec les champs attendus."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "number": 1,
                "description": {"fr": "Règle 1"},
                "goal": {"fr": ["Accessibilité"]},
                "metadata": {
                    "Tags": ["HTML"],
                    "Thématiques": ["Contenus"],
                    "Phases projet": ["Intégration"],
                },
                "slug": {"fr": "regle-1"},
            },
            {
                "id": 2,
                "number": 2,
                "description": {"fr": "Règle 2"},
                "goal": {"fr": ["Performance"]},
                "metadata": {
                    "Tags": ["CSS"],
                    "Thématiques": ["Navigation"],
                    "Phases projet": ["Design"],
                },
                "slug": {"fr": "regle-2"},
            },
        ]
        mock_get.return_value = mock_response

        rules = fetch_api()

        assert isinstance(rules, list)
        assert len(rules) == 2
        assert rules[0]["id"] == 1
        assert rules[0]["intitule"] == "Règle 1"
        assert rules[0]["theme"] == "Contenus"
        assert rules[1]["id"] == 2
        assert rules[1]["theme"] == "Navigation"

    @patch("app.ingestion.acquisition.requests.get")
    def test_fetch_api_accepts_empty_tags(self, mock_get):
        """Vérifie que fetch_api accepte une liste Tags vide."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 3,
                "number": 3,
                "description": {"fr": "Règle 3"},
                "goal": {"fr": ["Sécurité"]},
                "metadata": {
                    "Tags": [],
                    "Thématiques": ["Sécurité"],
                    "Phases projet": ["Développement"],
                },
                "slug": {"fr": "regle-3"},
            },
        ]
        mock_get.return_value = mock_response

        rules = fetch_api()

        assert rules[0]["tags"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_acquisition.py -v
```

Expected: FAIL — `pydantic_core._pydantic_core.ValidationError: 1 validation error for RuleAcquisition / theme / Field required`.

- [ ] **Step 3: Add theme mapping in acquisition.py**

Modify `app/ingestion/acquisition.py` — in `fetch_api()`, update the `RuleAcquisition(...)` construction:

```python
    for rule in rules_data:
        rule_acquisition = RuleAcquisition(
            id=rule["id"],
            number=rule["number"],
            intitule=rule["description"]["fr"],
            theme=rule["metadata"]["Thématiques"][0],
            objectifs=rule["goal"]["fr"],
            tags=rule["metadata"]["Tags"],
            phases=rule["metadata"]["Phases projet"],
            slug=rule["slug"]["fr"],
        )
        rules.append(rule_acquisition.model_dump())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_acquisition.py -v
```

Expected: All tests PASS (4 tests: `test_build_rule_url_basic`, `test_fetch_api_returns_list`, `test_fetch_api_accepts_empty_tags`, `test_scrape_rule_extracts_solution_and_controle`).

- [ ] **Step 5: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/acquisition.py tests/unit/ingestion/test_acquisition.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/acquisition.py tests/unit/ingestion/test_acquisition.py && git commit -m "feat: map metadata.Thématiques to theme in fetch_api()

- theme=rule[\"metadata\"][\"Thématiques\"][0] — API always returns a
  single-element list, extracted as scalar (RuleAcquisition.theme: str)

Tests: theme mapping verified, empty Tags list accepted

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Restore theme table in migration and SQLAlchemy models

**Files:**
- Modify: `app/migration/versions/0001_schema_initial.py`
- Modify: `app/models/referentiel.py`
- Modify: `tests/migration/test_migration.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `theme` table, `regle.theme_id` FK NOT NULL, SQLAlchemy `Theme` class

- [ ] **Step 1: Restore theme table creation in migration 0001**

Modify `app/migration/versions/0001_schema_initial.py` — in `upgrade()`, add the `theme` table before `objectif` and add `theme_id` to `regle`:

```python
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
```

Leave the rest of `upgrade()` unchanged (`objectif_regle`, `phase_regle`, `regle_tag`, core tables, indexes).

- [ ] **Step 2: Restore theme table drop in downgrade()**

Modify `app/migration/versions/0001_schema_initial.py` — in `downgrade()`, add `op.drop_table("theme")` at the end of the table-drop section (after `regle` is dropped, since `regle` references `theme`):

```python
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

- [ ] **Step 3: Restore Theme class and Regle.theme_id in referentiel.py**

Modify `app/models/referentiel.py` — add `Theme` class before `Regle` and add `theme_id` column:

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer, Numeric, PrimaryKeyConstraint, String, Text

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

- [ ] **Step 4: Update migration test expectations**

Modify `tests/migration/test_migration.py` — update `TABLES_ATTENDUES` and the docstring:

```python
TABLES_ATTENDUES = [
    "theme", "regle", "objectif", "phase", "tag",
    "objectif_regle", "phase_regle", "regle_tag",
    "utilisateur", "audit", "page", "audit_page", "audit_regle", "constat",
]

def test_toutes_les_tables_existent(conn):
    """Les 14 tables du MLD doivent toutes exister."""
```

- [ ] **Step 5: Re-apply migration on local database**

The Postgres container must be running first:

```bash
docker ps --format "{{.Names}}" | grep qualicheck-postgres
```

Expected: `qualicheck-postgres` printed. If not running: `cd /media/david/projets/QualiCheck && make up`.

Then downgrade and re-apply from repo root (both commands must run from `/media/david/projets/QualiCheck`, not from `app/migration/` — a relative-path mistake here previously left a stale `alembic_version` state):

```bash
cd /media/david/projets/QualiCheck && make downgrade
```

Expected: no error output.

```bash
cd /media/david/projets/QualiCheck && docker exec qualicheck-postgres psql -U "$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$(grep POSTGRES_DB .env | cut -d= -f2)" -c "\dt"
```

Expected: only `alembic_version` listed (or no tables at all) — confirms downgrade fully cleared the schema before re-applying. If `theme` or any other table is still present here, it's an orphan from a prior migration state — drop it manually before continuing:

```bash
docker exec qualicheck-postgres psql -U "$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$(grep POSTGRES_DB .env | cut -d= -f2)" -c "DROP TABLE IF EXISTS <orphan_table_name> CASCADE;"
```

```bash
cd /media/david/projets/QualiCheck && make migration
```

Expected: no error output.

```bash
docker exec qualicheck-postgres psql -U "$(grep POSTGRES_USER /media/david/projets/QualiCheck/.env | cut -d= -f2)" -d "$(grep POSTGRES_DB /media/david/projets/QualiCheck/.env | cut -d= -f2)" -c "\dt"
```

Expected: 15 rows listed (14 schema tables + `alembic_version`), including `theme`.

- [ ] **Step 6: Run migration tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/migration/ -v
```

Expected: 10 tests PASS.

- [ ] **Step 7: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/migration/versions/0001_schema_initial.py app/models/referentiel.py tests/migration/test_migration.py
```

Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add app/migration/versions/0001_schema_initial.py app/models/referentiel.py tests/migration/test_migration.py && git commit -m "fix: restore theme table and regle.theme_id in migration + models

Reverts the erroneous removal from a prior commit. theme is a simple 1-N
relation (regle.theme_id FK NOT NULL), not an association table — API
data confirms every rule has exactly one Thématiques value (245/245).

- Migration 0001 (never merged to main, modified in place): theme table
  restored in upgrade(), drop restored in downgrade()
- app/models/referentiel.py: Theme class + Regle.theme_id restored
- tests/migration/test_migration.py: 14 tables expected (was 13)
- Local DB: downgrade + re-migration verified, 10 migration tests passing

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Wire theme into stockage.py

**Files:**
- Modify: `app/ingestion/stockage.py`

**Interfaces:**
- Consumes: `Theme` (from `app.models.referentiel`, Task 3), `EnrichedRule.theme` (from Task 1)
- Produces: `upsert_rule()` now resolves and sets `regle.theme_id`

- [ ] **Step 1: Add Theme import and theme resolution in upsert_rule()**

Modify `app/ingestion/stockage.py`:

```python
"""
Étape 4 — Stockage du pipeline d'ingestion.

Persiste chaque EnrichedRule dans PostgreSQL : table regle + tables de
référence (theme, objectif, phase, tag) et leurs associations many-to-many.
"""

import logging

from sqlalchemy.orm import Session

from app.models.referentiel import (
    Objectif,
    ObjectifRegle,
    Phase,
    PhaseRegle,
    Regle,
    RegleTag,
    Tag,
    Theme,
)

from .aggregation import EnrichedRules
from .schema import EnrichedRule

logger = logging.getLogger(__name__)


def get_or_create(session: Session, model: type, **kwargs):
    """
    Cherche une ligne existante correspondant à kwargs, la crée si absente.

    Args:
        session: Session SQLAlchemy active
        model: Classe mappée (Theme, Objectif, Phase, ou Tag)
        kwargs: Critères de recherche/création (ex. tag="HTML")

    Returns:
        Instance existante ou nouvellement créée (pas de commit ici)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance

    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance


def upsert_rule(session: Session, enriched_rule: EnrichedRule) -> Regle:
    """
    Insère ou met à jour une Regle (upsert via numero), synchronise ses
    associations (objectif_regle, phase_regle, regle_tag) et son theme_id.

    Si numero existe déjà : UPDATE complet de tous les champs mutables.
    Si numero absent : INSERT.

    Args:
        session: Session SQLAlchemy active
        enriched_rule: Règle enrichie (Étape 3) à persister

    Returns:
        Instance Regle persistée (pas de commit ici)
    """
    regle = session.query(Regle).filter_by(numero=enriched_rule.number).first()

    if regle is None:
        regle = Regle(numero=enriched_rule.number)
        session.add(regle)

    theme = get_or_create(session, Theme, theme=enriched_rule.theme)
    regle.theme_id = theme.id

    regle.intitule = enriched_rule.intitule
    regle.solution = enriched_rule.solution
    regle.controle = enriched_rule.controle
    regle.strategie_analyse = enriched_rule.strategie_analyse
    regle.strategie_justification = enriched_rule.strategie_justification
    regle.strategie_source = enriched_rule.strategie_source
    regle.guide_analyse = enriched_rule.guide_analyse
    regle.llm_provider = enriched_rule.llm_provider

    session.flush()

    # -- Synchronise les associations many-to-many --------------------------
    session.query(ObjectifRegle).filter_by(regle_id=regle.id).delete()
    for objectif_nom in enriched_rule.objectifs:
        objectif = get_or_create(session, Objectif, objectif=objectif_nom)
        session.add(ObjectifRegle(objectif_id=objectif.id, regle_id=regle.id))

    session.query(PhaseRegle).filter_by(regle_id=regle.id).delete()
    for phase_nom in enriched_rule.phases:
        phase = get_or_create(session, Phase, phase=phase_nom)
        session.add(PhaseRegle(phase_id=phase.id, regle_id=regle.id))

    session.query(RegleTag).filter_by(regle_id=regle.id).delete()
    for tag_nom in enriched_rule.tags:
        tag = get_or_create(session, Tag, tag=tag_nom)
        session.add(RegleTag(regle_id=regle.id, tag_id=tag.id))

    session.flush()
    return regle


def store_rules(session: Session, enriched_rules: EnrichedRules) -> None:
    """
    Persiste toute la collection EnrichedRules dans une transaction unique.

    Fail-fast : si une règle échoue, rollback complet (aucune règle
    partiellement stockée), l'exception est relevée.

    Args:
        session: Session SQLAlchemy active
        enriched_rules: Collection EnrichedRules validée (Étape 3)

    Raises:
        Exception: Toute erreur de persistance (relevée après rollback)
    """
    try:
        for rule in enriched_rules.regles:
            upsert_rule(session, rule)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Règle {getattr(rule, 'number', '?')} — stockage : KO ({e})")
        raise

    logger.info(f"Stockage : {len(enriched_rules.regles)} règles stockées")
```

Note: `tags` loop already handles an empty list correctly (a `for` loop over `[]` simply does nothing) — no special-case needed for the now-optional `tags`.

- [ ] **Step 2: Manual verification — theme resolved and set on insert + update**

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
from pathlib import Path
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.referentiel import Regle, Theme, Tag, Objectif, Phase, ObjectifRegle, PhaseRegle, RegleTag
from app.ingestion.stockage import upsert_rule
from app.ingestion.schema import EnrichedRule

load_dotenv(Path(".env").resolve())
url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)

rule_v1 = EnrichedRule(
    id=999998, number=999998, intitule="Theme Test v1", theme="TestTheme",
    solution="Sol", controle="Ctrl", objectifs=["ObjThemeTest"], tags=[],
    phases=["PhaseThemeTest"], slug="theme-test-999998",
    strategie_analyse="statique", strategie_justification="J1", guide_analyse="G1"
)
rule_v2 = EnrichedRule(
    id=999998, number=999998, intitule="Theme Test v2", theme="TestTheme2",
    solution="Sol", controle="Ctrl", objectifs=["ObjThemeTest"], tags=[],
    phases=["PhaseThemeTest"], slug="theme-test-999998",
    strategie_analyse="statique", strategie_justification="J2", guide_analyse="G2"
)

with Session(engine) as session:
    regle1 = upsert_rule(session, rule_v1)
    session.commit()
    theme1_name = session.query(Theme).filter_by(id=regle1.theme_id).first().theme
    print(f"After insert: theme={theme1_name}, tags_count={session.query(RegleTag).filter_by(regle_id=regle1.id).count()}")

    regle2 = upsert_rule(session, rule_v2)
    session.commit()
    theme2_name = session.query(Theme).filter_by(id=regle2.theme_id).first().theme
    print(f"After update: theme={theme2_name}, same_row={regle1.id == regle2.id}")

    # Cleanup
    session.query(ObjectifRegle).filter_by(regle_id=regle2.id).delete()
    session.query(PhaseRegle).filter_by(regle_id=regle2.id).delete()
    session.delete(regle2)
    session.query(Theme).filter(Theme.theme.in_(["TestTheme", "TestTheme2"])).delete(synchronize_session=False)
    session.query(Objectif).filter_by(objectif="ObjThemeTest").delete()
    session.query(Phase).filter_by(phase="PhaseThemeTest").delete()
    session.commit()
EOF
```

Expected:
```
After insert: theme=TestTheme, tags_count=0
After update: theme=TestTheme2, same_row=True
```

- [ ] **Step 3: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/stockage.py
```

Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/stockage.py && git commit -m "feat: resolve and set theme_id in upsert_rule()

- get_or_create(session, Theme, theme=enriched_rule.theme) — same pattern
  as Objectif/Phase/Tag
- regle.theme_id set directly as a scalar FK (no association table,
  no delete-then-recreate — unlike objectifs/phases/tags)
- Empty tags list already handled correctly by the existing for loop

Vérifié manuellement : insert avec theme_id résolu, update change le
theme_id sur la même ligne.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Update Étape 3 (enrichment) test fixtures with theme

**Files:**
- Modify: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**
- Consumes: `Rule`/`EnrichedRule` now require `theme` (from Task 1)
- Produces: passing enrichment tests

- [ ] **Step 1: Add theme=... to every Rule/EnrichedRule construction**

Modify `tests/unit/ingestion/test_enrichment.py` — replace the entire file content:

```python
"""
Tests unitaires pour app/ingestion/enrichment.py et app/ingestion/llm_client.py

Teste l'enrichissement LLM de règles avec retry logic et parsing JSON.
"""

from unittest.mock import MagicMock, patch

from app.ingestion.aggregation import EnrichedRules, Rules
from app.ingestion.enrichment import enrich_rules
from app.ingestion.llm_client import LLMClient
from app.ingestion.schema import EnrichedRule
from app.ingestion.schema import RuleAggregation as Rule


class TestLLMClient:
    """Tests du client LangChain + Azure."""

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_enrich_single_rule_success(self, mock_azure_llm):
        """Enrichit une règle avec succès."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_response = MagicMock()
        mock_response.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Vérification simple du DOM", '
            '"guide_analyse": "Parcourez toutes les images et vérifiez l\'attribut alt."}'
        )
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Les images ont un attribut alt",
            theme="Images et médias",
            solution="Ajouter alt descriptif",
            controle="Vérifier alt présent",
            objectifs=["Accessibilité"],
            tags=["HTML"],
            phases=["Intégration"],
            slug="images-alt",
        )

        enriched = client.enrich_single_rule(rule)

        assert isinstance(enriched, EnrichedRule)
        assert enriched.strategie_analyse == "statique"
        assert enriched.strategie_justification == "Vérification simple du DOM"
        assert enriched.guide_analyse == "Parcourez toutes les images et vérifiez l'attribut alt."
        assert enriched.strategie_source == "ia_import"
        assert enriched.llm_provider == "kimi-k2.6"

    @patch("tenacity.nap.time.sleep")
    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_enrich_single_rule_retry_on_timeout(self, mock_azure_llm, mock_sleep):
        """Réessaie après timeout, puis réussit."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_response_success = MagicMock()
        mock_response_success.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Test", '
            '"guide_analyse": "Test guide"}'
        )

        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            mock_response_success,
        ]

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Test Rule",
            theme="Contenus",
            solution="Test solution",
            controle="Test control",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="test",
        )

        enriched = client.enrich_single_rule(rule)

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4)
        assert enriched.strategie_analyse == "statique"

    @patch("tenacity.nap.time.sleep")
    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_enrich_single_rule_fails_after_three_timeouts(self, mock_azure_llm, mock_sleep):
        """Lève une exception après 3 tentatives en échec."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Test Rule",
            theme="Contenus",
            solution="Test solution",
            controle="Test control",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="test",
        )

        try:
            client.enrich_single_rule(rule)
            raise AssertionError("Should have raised TimeoutError")
        except TimeoutError:
            pass

        assert mock_llm_instance.invoke.call_count == 3


class TestEnrichRules:
    """Tests de la fonction orchestration enrich_rules()."""

    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_transforms_collection(self, mock_llm_client_class):
        """Transforme une collection Rules en EnrichedRules."""
        rule1 = Rule(
            id=1,
            number=1,
            intitule="Rule 1",
            theme="Contenus",
            solution="Sol 1",
            controle="Ctrl 1",
            objectifs=["Obj1"],
            tags=["Tag1"],
            phases=["Phase1"],
            slug="rule-1",
        )
        rule2 = Rule(
            id=2,
            number=2,
            intitule="Rule 2",
            theme="Navigation",
            solution="Sol 2",
            controle="Ctrl 2",
            objectifs=["Obj2"],
            tags=["Tag2"],
            phases=["Phase2"],
            slug="rule-2",
        )
        rules = Rules([rule1, rule2])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1,
            number=1,
            intitule="Rule 1",
            theme="Contenus",
            solution="Sol 1",
            controle="Ctrl 1",
            objectifs=["Obj1"],
            tags=["Tag1"],
            phases=["Phase1"],
            slug="rule-1",
            strategie_analyse="statique",
            strategie_justification="Expl 1",
            guide_analyse="Guide 1",
        )
        enriched2 = EnrichedRule(
            id=2,
            number=2,
            intitule="Rule 2",
            theme="Navigation",
            solution="Sol 2",
            controle="Ctrl 2",
            objectifs=["Obj2"],
            tags=["Tag2"],
            phases=["Phase2"],
            slug="rule-2",
            strategie_analyse="playwright",
            strategie_justification="Expl 2",
            guide_analyse="Guide 2",
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        enriched_rules = enrich_rules(rules)

        assert isinstance(enriched_rules, EnrichedRules)
        assert len(enriched_rules.enriched_rules) == 2
        assert enriched_rules.enriched_rules[0].strategie_analyse == "statique"
        assert enriched_rules.enriched_rules[1].strategie_analyse == "playwright"

    @patch("app.ingestion.enrichment.logger")
    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_logs_on_all_timeouts(self, mock_llm_client_class, mock_logger):
        """Logue erreur critique si les 3 tentatives timeout."""
        rule = Rule(
            id=42,
            number=42,
            intitule="Rule 42",
            theme="Contenus",
            solution="Sol",
            controle="Ctrl",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="rule-42",
        )
        rules = Rules([rule])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance
        mock_llm_instance.enrich_single_rule.side_effect = TimeoutError(
            "All retries exhausted"
        )

        try:
            enrich_rules(rules)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

        mock_logger.error.assert_called()
        call_args = str(mock_logger.error.call_args)
        assert "42" in call_args
        assert "enrichissement" in call_args
        assert "KO" in call_args

    @patch("app.ingestion.enrichment.logger")
    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_logs_success_summary(self, mock_llm_client_class, mock_logger):
        """Logue le résumé de succès."""
        rule1 = Rule(
            id=1,
            number=1,
            intitule="R1",
            theme="Contenus",
            solution="S1",
            controle="C1",
            objectifs=["O1"],
            tags=["T1"],
            phases=["P1"],
            slug="r1",
        )
        rule2 = Rule(
            id=2,
            number=2,
            intitule="R2",
            theme="Navigation",
            solution="S2",
            controle="C2",
            objectifs=["O2"],
            tags=["T2"],
            phases=["P2"],
            slug="r2",
        )
        rules = Rules([rule1, rule2])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1,
            number=1,
            intitule="R1",
            theme="Contenus",
            solution="S1",
            controle="C1",
            objectifs=["O1"],
            tags=["T1"],
            phases=["P1"],
            slug="r1",
            strategie_analyse="statique",
            strategie_justification="X",
            guide_analyse="Y",
        )
        enriched2 = EnrichedRule(
            id=2,
            number=2,
            intitule="R2",
            theme="Navigation",
            solution="S2",
            controle="C2",
            objectifs=["O2"],
            tags=["T2"],
            phases=["P2"],
            slug="r2",
            strategie_analyse="playwright",
            strategie_justification="X",
            guide_analyse="Y",
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        enrich_rules(rules)

        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        assert "Enrichissement" in call_args
        assert "2" in call_args
        assert "règles enrichies" in call_args
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichment.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check tests/unit/ingestion/test_enrichment.py
```

Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add tests/unit/ingestion/test_enrichment.py && git commit -m "test: add theme field to enrichment test fixtures

Rule/EnrichedRule now require theme (Task 1) — updated all 11
constructions across the 6 enrichment tests.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Full unit + migration test suite verification

**Files:**
- None created — final verification pass

**Interfaces:**
- Consumes: all prior tasks
- Produces: confirmation that the whole test suite is green

- [ ] **Step 1: Run all unit tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ -v
```

Expected: All tests PASS. Count: 3 (acquisition, now 4 with the new empty-tags test — see Task 2) + ~15 (aggregation, per Task 1) + 6 (enrichment) = ~25 tests, all green, zero failures.

- [ ] **Step 2: Run migration tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/migration/ -v
```

Expected: 10 tests PASS.

- [ ] **Step 3: Full lint pass**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ tests/ scripts/
```

Expected: `All checks passed!`

- [ ] **Step 4: Real end-to-end smoke test (optional but recommended) — 1 rule, real API + real LLM**

This confirms the whole pipeline works with theme wired in, using a real Opquast rule and a real (paid) LLM call. Skip this step if you'd rather not spend an LLM call right now — Tasks 1-5's tests already give strong confidence.

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
from pathlib import Path
import os, logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.logging_config import setup_logging
from app.ingestion.acquisition import acquire_rules
from app.ingestion.aggregation import aggregate_rules
from app.ingestion.enrichment import enrich_rules
from app.ingestion.stockage import store_rules
from app.models.referentiel import Theme

setup_logging()
load_dotenv(Path(".env").resolve())
logger = logging.getLogger("validation")

all_rules = acquire_rules()
acquired = [r for r in all_rules if r["tags"] and r["objectifs"] and r["phases"]][:1]
print("Acquired:", [(r["number"], r["theme"]) for r in acquired])

rules = aggregate_rules(acquired)
enriched = enrich_rules(rules)

url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)
with Session(engine) as session:
    store_rules(session, enriched)
    from app.models.referentiel import Regle
    regle = session.query(Regle).filter_by(numero=acquired[0]["number"]).first()
    theme = session.query(Theme).filter_by(id=regle.theme_id).first()
    print(f"Stored: numero={regle.numero}, theme={theme.theme}, embedding_null={regle.embedding is None}")
EOF
```

Expected: prints the acquired rule's theme, then confirms it was stored with a resolved `theme_id` and `embedding_null=True`.

- [ ] **Step 5: No commit needed for this task** — verification only, no file changes.

---

## Summary

✅ **Theme restoration + tags optional** fully implemented:

- **Pydantic models:** `theme: str` on `RuleAcquisition`/`RuleAggregation` (validated non-empty), `tags` no longer validated (empty list accepted)
- **Acquisition:** `metadata.Thématiques[0]` mapped to `theme`
- **Schema:** `theme` table + `regle.theme_id` FK NOT NULL restored in migration 0001 and `app/models/referentiel.py`
- **Storage:** `upsert_rule()` resolves `theme` via `get_or_create()` and sets `regle.theme_id` directly (scalar FK, no association table)
- **Tests:** all fixtures across acquisition/aggregation/enrichment updated with `theme=...`; migration tests expect 14 tables again; new tests cover empty-tags acceptance and theme validation

**Data note:** the 3 previously-stored validation rules (numero 1, 3, 4) were wiped by the downgrade/re-migration cycle in Task 3 — they lacked `theme_id` since that column didn't exist when they were stored. No data migration was needed per the approved spec.

**Next stage:** Étape 5 — Chunking (not covered by this plan).
