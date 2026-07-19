# Étape 4 — Stockage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist each `EnrichedRule` from the Étape 3 output into PostgreSQL (`regle` table + reference tables `objectif`/`phase`/`tag` and their associations), with idempotent upsert via `numero`, then wire acquisition → aggregation → enrichment → stockage into a first version of `scripts/ingestion.py`.

**Architecture:**
- `app/ingestion/stockage.py` provides `get_or_create()` (generic, reused for Objectif/Phase/Tag), `upsert_rule()` (insert-or-update on `Regle.numero`), and `store_rules()` (orchestrates the whole `EnrichedRules` collection inside one transaction, fail-fast with rollback).
- `scripts/ingestion.py` is a new CLI entry point chaining the four existing pipeline stages, with per-stage logging and a non-zero exit code on failure.
- No pytest suite for this stage — validation happens by running `scripts/ingestion.py` for real and inspecting the database directly (per the approved spec).

**Tech Stack:** SQLAlchemy 2.x ORM (session-based), PostgreSQL via psycopg2, existing Pydantic models from `app/ingestion/schema.py`, existing SQLAlchemy models from `app/models/referentiel.py`.

## Global Constraints

- **Code:** English (function/class/variable names) — `get_or_create`, `upsert_rule`, `store_rules`
- **Docs/comments/logs:** French
- **Fail-fast:** any exception during storage of any rule → `session.rollback()`, log error, re-raise — no partial writes across the whole `EnrichedRules` collection
- **Transaction scope:** ONE transaction for the entire `EnrichedRules` collection, not per-rule
- **Embedding column:** stays `NULL` at this stage — never written by `stockage.py` in this plan (Étape 7 writes it later)
- **Upsert semantics:** if `Regle.numero` already exists, UPDATE every mutable column (`intitule`, `solution`, `controle`, `strategie_analyse`, `strategie_justification`, `strategie_source`, `guide_analyse`, `llm_provider`) — never skip
- **Logging (stockage.py):** error per failing rule (`logger.error`), one summary on full success (`logger.info`) — no per-rule success log
- **Logging (scripts/ingestion.py):** start/end log per stage, explicit failing-stage log before `sys.exit(1)`
- **DB connection:** build the SQLAlchemy URL from `.env` vars `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` using the exact same pattern as `app/migration/env.py:get_url()` (`postgresql+psycopg2://...`)
- **No tests written in this plan** — verification is via `make up` + `make migration` + running the script manually and reading `logs/ingestion.log` + inspecting tables via `psql`

---

## Task 1: Implement `get_or_create()` in stockage.py

**Files:**
- Create: `app/ingestion/stockage.py`

**Interfaces:**
- Consumes: `sqlalchemy.orm.Session`, any mapped class from `app.models.referentiel` (`Objectif`, `Phase`, `Tag`)
- Produces: `get_or_create(session: Session, model: type, **kwargs) -> Base` — returns the existing or newly created instance. Does not commit (caller controls the transaction).

- [ ] **Step 1: Create the file with imports and get_or_create()**

Create `app/ingestion/stockage.py`:

```python
"""
Étape 4 — Stockage du pipeline d'ingestion.

Persiste chaque EnrichedRule dans PostgreSQL : table regle + tables de
référence (objectif, phase, tag) et leurs associations many-to-many.
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
)

from .aggregation import EnrichedRules
from .schema import EnrichedRule

logger = logging.getLogger(__name__)


def get_or_create(session: Session, model: type, **kwargs):
    """
    Cherche une ligne existante correspondant à kwargs, la crée si absente.

    Args:
        session: Session SQLAlchemy active
        model: Classe mappée (Objectif, Phase, ou Tag)
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
```

- [ ] **Step 2: Manual verification against a running database**

This requires the Postgres container running and migration applied — confirm first:

```bash
cd /media/david/projets/QualiCheck && docker ps --format "{{.Names}}" | grep qualicheck-postgres
```

Expected: `qualicheck-postgres` printed. If not running, run `make up` then `make migration` before continuing.

Then verify `get_or_create` works and is idempotent:

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.referentiel import Tag
from app.ingestion.stockage import get_or_create

load_dotenv()
url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)

with Session(engine) as session:
    tag1 = get_or_create(session, Tag, tag="HTML")
    tag2 = get_or_create(session, Tag, tag="HTML")
    session.commit()
    print(f"tag1.id={tag1.id}, tag2.id={tag2.id}, same={tag1.id == tag2.id}")
    session.query(Tag).filter_by(tag="HTML").delete()
    session.commit()
EOF
```

Expected: `tag1.id=<some-int>, tag2.id=<same-int>, same=True` — proves get_or_create doesn't create a duplicate row on the second call. The cleanup line removes the test row afterward.

- [ ] **Step 3: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/stockage.py
```

Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/stockage.py && git commit -m "feat: implement get_or_create() for reference tables (Étape 4)

- Fonction générique réutilisée pour Objectif, Phase, Tag
- Cherche par kwargs, crée si absent, flush (pas de commit — le caller
  contrôle la transaction)
- Idempotent : vérifié manuellement (deux appels identiques → même id)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Implement `upsert_rule()`

**Files:**
- Modify: `app/ingestion/stockage.py`

**Interfaces:**
- Consumes: `get_or_create()` (Task 1), `sqlalchemy.orm.Session`, `EnrichedRule` (from `app.ingestion.schema`)
- Produces: `upsert_rule(session: Session, enriched_rule: EnrichedRule) -> Regle` — the persisted `Regle` ORM instance (inserted or updated), with reference tables and associations synced. Does not commit.

- [ ] **Step 1: Add upsert_rule() to stockage.py**

Append to `app/ingestion/stockage.py`:

```python


def upsert_rule(session: Session, enriched_rule: EnrichedRule) -> Regle:
    """
    Insère ou met à jour une Regle (upsert via numero), synchronise ses
    associations (objectif_regle, phase_regle, regle_tag).

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
```

**Design note on association sync:** deleting all existing associations for the rule and re-creating them from the current `EnrichedRule` data is simpler and correct for both insert and update cases — avoids diffing old vs new lists. At MVP scale (245 rules, few associations each) the extra deletes are negligible cost.

- [ ] **Step 2: Manual verification — insert then update same numero**

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.referentiel import Regle, Tag
from app.ingestion.stockage import upsert_rule
from app.ingestion.schema import EnrichedRule

load_dotenv()
url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)

rule_v1 = EnrichedRule(
    id=999999, number=999999, intitule="Test v1", solution="Sol v1", controle="Ctrl v1",
    objectifs=["ObjTest"], tags=["TagTest"], phases=["PhaseTest"], slug="test-999999",
    strategie_analyse="statique", strategie_justification="J1", guide_analyse="G1"
)
rule_v2 = EnrichedRule(
    id=999999, number=999999, intitule="Test v2 (updated)", solution="Sol v2", controle="Ctrl v2",
    objectifs=["ObjTest"], tags=["TagTest"], phases=["PhaseTest"], slug="test-999999",
    strategie_analyse="playwright", strategie_justification="J2", guide_analyse="G2"
)

with Session(engine) as session:
    regle1 = upsert_rule(session, rule_v1)
    session.commit()
    id_after_insert = regle1.id

    regle2 = upsert_rule(session, rule_v2)
    session.commit()

    print(f"same_row={id_after_insert == regle2.id}, intitule={regle2.intitule}, strategie={regle2.strategie_analyse}")

    # Cleanup
    session.query(Regle).filter_by(numero=999999).delete()
    session.query(Tag).filter_by(tag="TagTest").delete()
    session.commit()
EOF
```

Expected: `same_row=True, intitule=Test v2 (updated), strategie=playwright` — proves the second call updated the existing row (same id) rather than inserting a duplicate.

- [ ] **Step 3: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/stockage.py
```

Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/stockage.py && git commit -m "feat: implement upsert_rule() with association sync (Étape 4)

- Upsert Regle via numero : UPDATE complet si présent, INSERT sinon
- embedding jamais touché ici (reste NULL, écrit à l'Étape 7)
- Synchronise objectif_regle/phase_regle/regle_tag : delete puis recrée
  depuis les données courantes (simple et correct pour insert et update)
- Vérifié manuellement : insert puis update sur le même numero → même id,
  champs mis à jour

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Implement `store_rules()` orchestration

**Files:**
- Modify: `app/ingestion/stockage.py`

**Interfaces:**
- Consumes: `upsert_rule()` (Task 2), `EnrichedRules` (from `app.ingestion.aggregation`), `sqlalchemy.orm.Session`
- Produces: `store_rules(session: Session, enriched_rules: EnrichedRules) -> None` — commits on full success, rolls back and re-raises on any failure

- [ ] **Step 1: Add store_rules() to stockage.py**

Append to `app/ingestion/stockage.py`:

```python


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

- [ ] **Step 2: Manual verification — full collection commits together**

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.referentiel import Regle, Tag
from app.ingestion.stockage import store_rules
from app.ingestion.schema import EnrichedRule
from app.ingestion.aggregation import EnrichedRules

load_dotenv()
url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)

rules = [
    EnrichedRule(
        id=999001, number=999001, intitule="Batch 1", solution="S1", controle="C1",
        objectifs=["ObjBatch"], tags=["TagBatch"], phases=["PhaseBatch"], slug="batch-1",
        strategie_analyse="statique", strategie_justification="J", guide_analyse="G"
    ),
    EnrichedRule(
        id=999002, number=999002, intitule="Batch 2", solution="S2", controle="C2",
        objectifs=["ObjBatch"], tags=["TagBatch"], phases=["PhaseBatch"], slug="batch-2",
        strategie_analyse="playwright", strategie_justification="J", guide_analyse="G"
    ),
]
collection = EnrichedRules(rules)

with Session(engine) as session:
    store_rules(session, collection)
    count = session.query(Regle).filter(Regle.numero.in_([999001, 999002])).count()
    print(f"stored_count={count}")

    # Cleanup
    session.query(Regle).filter(Regle.numero.in_([999001, 999002])).delete(synchronize_session=False)
    session.query(Tag).filter_by(tag="TagBatch").delete()
    session.commit()
EOF
```

Expected: `stored_count=2` — both rules committed together.

- [ ] **Step 3: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/stockage.py
```

Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/stockage.py && git commit -m "feat: implement store_rules() orchestration (Étape 4)

- Une transaction globale pour toute la collection EnrichedRules
- Fail-fast : rollback complet + log erreur + re-raise si une règle échoue
- Log de synthèse en succès (X règles stockées)
- Vérifié manuellement : deux règles stockées ensemble, commit unique

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Create scripts/ingestion.py (partial orchestrator)

**Files:**
- Create: `scripts/ingestion.py`

**Interfaces:**
- Consumes: `acquire_rules()` (from `app.ingestion.acquisition`), `aggregate_rules()` (from `app.ingestion.aggregation`), `enrich_rules()` (from `app.ingestion.enrichment`), `store_rules()` (from `app.ingestion.stockage`, Task 3), `setup_logging()` (from `app.logging_config`)
- Produces: CLI entry point, run via `uv run python scripts/ingestion.py`. Exits 0 on full success, non-zero on any stage failure.

- [ ] **Step 1: Create scripts/ingestion.py**

Create `scripts/ingestion.py`:

```python
"""Point d'entrée pour le pipeline d'ingestion complet.

Orchestre les étapes du pipeline en séquence (acquisition → agrégation →
enrichissement → stockage), applique le principe fail-fast : toute erreur
sur une étape arrête immédiatement le script avec un code de sortie non-nul.

Étapes 5-7 (chunking, embedding, indexation) pas encore implémentées —
seront ajoutées à ce même script dans une session future.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.acquisition import acquire_rules  # noqa: E402
from app.ingestion.aggregation import aggregate_rules  # noqa: E402
from app.ingestion.enrichment import enrich_rules  # noqa: E402
from app.ingestion.stockage import store_rules  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def main() -> None:
    setup_logging()
    load_dotenv()

    logger.info("=== Pipeline d'ingestion : démarrage ===")

    try:
        logger.info("Étape 1 — Acquisition : démarrage")
        acquired = acquire_rules()
        logger.info("Étape 1 — Acquisition : terminée (%d règles)", len(acquired))
    except Exception as e:
        logger.error("Étape 1 — Acquisition : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 2 — Agrégation : démarrage")
        rules = aggregate_rules(acquired)
        logger.info("Étape 2 — Agrégation : terminée")
    except Exception as e:
        logger.error("Étape 2 — Agrégation : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 3 — Enrichissement : démarrage")
        enriched = enrich_rules(rules)
        logger.info("Étape 3 — Enrichissement : terminée")
    except Exception as e:
        logger.error("Étape 3 — Enrichissement : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 4 — Stockage : démarrage")
        engine = get_engine()
        with Session(engine) as session:
            store_rules(session, enriched)
        logger.info("Étape 4 — Stockage : terminée")
    except Exception as e:
        logger.error("Étape 4 — Stockage : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== Pipeline d'ingestion : succès (Étapes 1-4) ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Lint check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check scripts/ingestion.py
```

Expected: `All checks passed!` (if `noqa: E402` comments trigger anything unexpected, fix per ruff's exact message — the pattern mirrors `app/migration/env.py` which already uses the same sys.path trick)

- [ ] **Step 3: Commit**

```bash
git add scripts/ingestion.py && git commit -m "feat: add scripts/ingestion.py orchestrator (Étapes 1-4)

- Chaîne acquisition → aggregation → enrichment → stockage
- Fail-fast : log explicite de l'étape en échec + sys.exit(1)
- Log de début/fin par étape
- Connexion DB construite depuis .env (même pattern que app/migration/env.py)
- Étapes 5-7 (chunking, embedding, indexation) pas encore implémentées —
  à ajouter dans une session future

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Real end-to-end validation run

**Files:**
- None created — this task runs the pipeline for real and inspects the database

**Interfaces:**
- Consumes: `scripts/ingestion.py` (Task 4), running Postgres container, live Azure/Opquast credentials in `.env`
- Produces: populated `regle`/`objectif`/`phase`/`tag` tables + association tables, `logs/ingestion.log` entries to review

**Cost warning:** this calls the real Opquast API/site (free) AND the real Azure LLM (Kimi K2.6) for every rule acquired — 245 calls if run unmodified. Read Step 1 before running.

- [ ] **Step 1: Decide and apply a rule-count limit for the validation run**

Since `acquire_rules()` has no built-in limit, temporarily slice the list before aggregation to avoid paying for 245 LLM calls during validation. Run this modified check in a Python REPL rather than editing production code:

```bash
cd /media/david/projets/QualiCheck && uv run python3 << 'EOF'
from dotenv import load_dotenv
import os, logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.logging_config import setup_logging
from app.ingestion.acquisition import acquire_rules
from app.ingestion.aggregation import aggregate_rules
from app.ingestion.enrichment import enrich_rules
from app.ingestion.stockage import store_rules

setup_logging()
load_dotenv()
logger = logging.getLogger("validation")

logger.info("=== Validation run : démarrage (3 règles) ===")

acquired = acquire_rules()[:3]
logger.info("Acquisition OK : %d règles", len(acquired))

rules = aggregate_rules(acquired)
logger.info("Agrégation OK")

enriched = enrich_rules(rules)
logger.info("Enrichissement OK")

url = f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
engine = create_engine(url)
with Session(engine) as session:
    store_rules(session, enriched)

logger.info("=== Validation run : succès ===")
EOF
```

Expected: script completes without exception, prints nothing to console (logging is file-only per `app/logging_config.py`).

- [ ] **Step 2: Review the log file**

```bash
tail -40 /media/david/projets/QualiCheck/logs/ingestion.log
```

Expected: entries showing acquisition, agrégation, enrichissement, and stockage log lines, ending with `Stockage : 3 règles stockées`, no `KO` or `ÉCHEC` lines from this run.

- [ ] **Step 3: Inspect the database directly**

```bash
docker exec -it qualicheck-postgres psql -U "$(grep POSTGRES_USER /media/david/projets/QualiCheck/.env | cut -d= -f2)" -d "$(grep POSTGRES_DB /media/david/projets/QualiCheck/.env | cut -d= -f2)" -c "SELECT numero, intitule, strategie_analyse, embedding IS NULL AS embedding_null FROM regle ORDER BY numero LIMIT 5;"
```

Expected: 3 rows (or however many were validated), `embedding_null` is `t` (true) for all — confirms embedding is correctly left NULL at this stage.

```bash
docker exec -it qualicheck-postgres psql -U "$(grep POSTGRES_USER /media/david/projets/QualiCheck/.env | cut -d= -f2)" -d "$(grep POSTGRES_DB /media/david/projets/QualiCheck/.env | cut -d= -f2)" -c "SELECT COUNT(*) FROM regle_tag; SELECT COUNT(*) FROM objectif_regle; SELECT COUNT(*) FROM phase_regle;"
```

Expected: non-zero counts on all three, confirming associations were created.

- [ ] **Step 4: Re-run the same validation script to confirm idempotence**

Run the exact same script from Step 1 again.

```bash
docker exec -it qualicheck-postgres psql -U "$(grep POSTGRES_USER /media/david/projets/QualiCheck/.env | cut -d= -f2)" -d "$(grep POSTGRES_DB /media/david/projets/QualiCheck/.env | cut -d= -f2)" -c "SELECT COUNT(*) FROM regle;"
```

Expected: same total row count as after Step 1 (no duplicates created — proves upsert idempotence on real data, not just the synthetic numero=999xxx rows from Tasks 1-3).

- [ ] **Step 5: Clean up validation data**

The 3 rules acquired in Step 1 are real Opquast rules (not throwaway numero=999xxx test data) — decide with the user whether to keep them in the dev database or remove them:

```bash
# Only run if you want to remove the validation rows — ask the user first
# docker exec -it qualicheck-postgres psql -U "$(grep POSTGRES_USER /media/david/projets/QualiCheck/.env | cut -d= -f2)" -d "$(grep POSTGRES_DB /media/david/projets/QualiCheck/.env | cut -d= -f2)" -c "DELETE FROM regle WHERE numero IN (<numeros from Step 1 output>);"
```

No commit needed for this task — it's a validation exercise, not a code change.

---

## Task 6: Update documentation and CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `TODO_PIPELINE_INGESTION.md`

**Interfaces:**
- Consumes: all tasks completed
- Produces: updated project tracking

- [ ] **Step 1: Update CHANGELOG.md**

Add a new entry at the top of `CHANGELOG.md`, right after the header/format block, following the existing entry format (check the file first — entries are prepended, most recent first):

```markdown
## 2026-07-19 — Claude Code (Part 3)

- **Étape 4 — Stockage (pipeline d'ingestion)** — voir `app/ingestion/stockage.py`, `scripts/ingestion.py`
  - `get_or_create()` : fonction générique idempotente pour Objectif/Phase/Tag
  - `upsert_rule()` : upsert Regle via numero (UPDATE complet si présent, INSERT sinon), synchronise les associations many-to-many (delete + recrée)
  - `store_rules()` : orchestration de toute la collection EnrichedRules dans une transaction unique, fail-fast avec rollback complet
  - `embedding` reste NULL à cette étape (écrit plus tard, Étape 7)
  - `scripts/ingestion.py` : première version, orchestre Étapes 1-4, fail-fast avec log explicite par étape et code de sortie non-nul
  - Pas de suite pytest pour cette étape — validation par exécution réelle du script + inspection directe des tables PostgreSQL (voir Task 5 du plan d'implémentation)
  - Correctif préalable : suppression de `theme`/`theme_id` du MCD (erreur de conception, relation déjà couverte par `tag`)
```

- [ ] **Step 2: Update TODO_PIPELINE_INGESTION.md**

Read the file first to see the exact current state of the Étape 4 checklist item, then mark it complete following the same pattern used for Étapes 1-3 (checked boxes, "Tests passants ✅" replaced with a note about manual validation since there's no automated suite):

```markdown
- [x] **Étape 4 — Stockage**
  - [x] `app/ingestion/stockage.py`
  - [x] `get_or_create()` : générique, idempotent (Objectif/Phase/Tag)
  - [x] `upsert_rule()` : upsert via numero, sync associations
  - [x] `store_rules()` : transaction globale, fail-fast, logging
  - [x] `scripts/ingestion.py` : orchestrateur partiel (Étapes 1-4)
  - Validation par exécution réelle + inspection BDD (pas de suite pytest) ✅
```

- [ ] **Step 3: Commit documentation updates**

```bash
git add CHANGELOG.md TODO_PIPELINE_INGESTION.md && git commit -m "docs: update CHANGELOG and TODO for Étape 4 completion

- Étape 4 (Stockage) : terminée ✅
- scripts/ingestion.py : orchestrateur partiel (Étapes 1-4)
- Prêt pour Étape 5 (Chunking)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Summary

✅ **Étape 4 — Stockage** fully implemented:

- **`get_or_create()`**: generic idempotent lookup-or-insert for reference tables
- **`upsert_rule()`**: insert-or-full-update on `Regle.numero`, association sync via delete-then-recreate, `embedding` untouched
- **`store_rules()`**: single-transaction orchestration across the whole `EnrichedRules` collection, fail-fast with rollback
- **`scripts/ingestion.py`**: new CLI orchestrator chaining Étapes 1-4, per-stage logging, non-zero exit on failure
- **Validation**: real end-to-end run (limited rule count to control LLM cost) + log review + direct SQL inspection — no pytest suite, per approved spec
- **Prerequisite fix**: removed erroneous `theme`/`theme_id` from schema (already done in a prior commit, referenced here for completeness)

**Next stage**: Étape 5 — Chunking (not covered by this plan).
