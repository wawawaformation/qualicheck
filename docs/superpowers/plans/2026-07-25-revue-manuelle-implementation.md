# Revue Manuelle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter 3 colonnes nullables à `regle` (`reviewed_at`, `review_status`, `review_note`) pour tracer en base la revue manuelle des classifications LLM, sans toucher au code du pipeline d'ingestion.

**Architecture:** Migration Alembic pure + modèle SQLAlchemy — aucune logique applicative, aucun champ Pydantic. Ces colonnes ne sont jamais lues ni écrites par `app/ingestion/`, uniquement renseignées manuellement (`psql`) après une revue humaine.

**Tech Stack:** SQLAlchemy + Alembic (migration), psycopg2 (tests d'intégration migration).

**Spec source:** `conception/2_ingestion/G_revue_manuelle.md` (ne pas modifier son contenu dans ce plan — seuls le modèle, la migration, les docs et les tests changent).

## Global Constraints

- Les 3 colonnes sont **nullables** — aucune règle n'a de valeur au moment de cette migration (spec §4.2).
- **Aucun code de pipeline ne doit référencer ces colonnes** (`app/ingestion/schema.py`, `llm_client.py`, `stockage.py`) — spec §2, vérifié par grep (spec §6.4).
- `review_status` : vocabulaire fermé `valide`/`a_revoir`/`invalide`, porté par convention (pas de `CHECK` ni d'enum PostgreSQL) — cohérent avec `strategie_analyse` (spec §3, §5).
- Nommage technique (anglais) — métadonnée de pipeline, pas vocabulaire du domaine Opquast (spec §2).
- `ruff check` propre et `pytest` vert avant tout commit (`CLAUDE.md` racine du projet).
- Commits : titre en anglais, corps en français (`~/.claude/CLAUDE.md`).

---

### Task 1: Migration 0010 + modèle `Regle` + tests + documentation

**Files:**
- Modify: `app/models/referentiel.py`
- Create: `app/migration/versions/0010_add_manual_review_columns.py`
- Modify: `tests/migration/test_migration.py`
- Modify: `conception/2_ingestion/MLD_qualicheck.md`
- Modify: `conception/annexes/MLD_qualicheck.md`

**Interfaces:**
- Consumes: aucune (couche BDD/modèle, pas de dépendance à du code applicatif).
- Produces: colonnes `regle.reviewed_at` (DateTime, nullable), `regle.review_status` (String(16), nullable), `regle.review_note` (Text, nullable) — consommées par personne dans ce chantier, uniquement requêtables manuellement.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `tests/migration/test_migration.py`, après `test_colonnes_provenance_regle` (et avant `test_colonne_llm_provider_absente`), ajouter :

```python
def test_colonnes_revue_manuelle_regle(conn):
    """Les 3 colonnes de revue manuelle doivent exister sur regle, toutes nullables."""
    colonnes = ["reviewed_at", "review_status", "review_note"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'regle'
            AND column_name = ANY(%s);
        """, (colonnes,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    manquantes = set(colonnes) - set(rows)
    assert not manquantes, f"Colonnes revue manuelle manquantes : {manquantes}"
    non_nullable = [col for col in colonnes if rows.get(col) != "YES"]
    assert not non_nullable, f"Colonnes revue manuelle incorrectement NOT NULL : {non_nullable}"
```

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `make up && make migration && uv run pytest tests/migration/test_migration.py -v -k "revue_manuelle"`
Expected: FAIL (`Colonnes revue manuelle manquantes : {'reviewed_at', 'review_status', 'review_note'}`).

- [ ] **Step 3: Modifier `app/models/referentiel.py`**

Ajouter les 3 colonnes sur `Regle`, après `updated_at` et avant `embedding` :

```python
    reviewed_at = Column(DateTime, nullable=True)
    review_status = Column(String(16), nullable=True)
    review_note = Column(Text, nullable=True)
    embedding = Column(Vector(384))
```

(remplace la ligne `embedding = Column(Vector(384))` existante par les 4 lignes ci-dessus — `DateTime`, `String`, `Text` sont déjà importés en tête de fichier, aucun nouvel import nécessaire.)

- [ ] **Step 4: Créer la migration `0010_add_manual_review_columns.py`**

```python
"""Add manual review columns to regle (reviewed_at, review_status, review_note)

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("regle", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("regle", sa.Column("review_status", sa.String(16), nullable=True))
    op.add_column("regle", sa.Column("review_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("regle", "review_note")
    op.drop_column("regle", "review_status")
    op.drop_column("regle", "reviewed_at")
```

- [ ] **Step 5: Run pour vérifier le succès**

Run: `make migration && uv run pytest tests/migration/test_migration.py -v`
Expected: tous les tests PASS, y compris `test_colonnes_revue_manuelle_regle`.

- [ ] **Step 6: Vérifier le downgrade (retester une migration from scratch)**

Run: `make downgrade && make migration && uv run pytest tests/migration/test_migration.py -v`
Expected: tous les tests PASS à nouveau (up/down/up symétrique).

- [ ] **Step 7: Documenter les 3 colonnes dans le MLD**

Dans `conception/2_ingestion/MLD_qualicheck.md`, section `### regle`, remplacer :

```text
  embedding *             vector(384)               -- All MiniLM L12 v2, index HNSW
)
```

par :

```text
  reviewed_at *           TIMESTAMP                 -- NULL = pas encore revue manuellement
  review_status *         VARCHAR(16)               -- valide | a_revoir | invalide
  review_note *           TEXT                      -- notes de revue, matière pour un futur script de réécriture ciblée
  embedding *             vector(384)               -- All MiniLM L12 v2, index HNSW
)
```

Appliquer le même changement dans `conception/annexes/MLD_qualicheck.md` (copie
actuellement identique, cf. Task 9 de la spec E qui les avait déjà synchronisées).

- [ ] **Step 8: Vérifier l'absence de référence dans le code du pipeline (spec §6.4)**

Run: `grep -rn "review_status\|review_note\|reviewed_at" app/ingestion/`
Expected: aucune sortie (aucun code du pipeline ne référence ces colonnes).

- [ ] **Step 9: Suite complète + lint**

Run: `uv run pytest tests/ -v && uv run ruff check .`
Expected: tous les tests PASS, `ruff` propre.

- [ ] **Step 10: Vérifier le périmètre du diff**

Run: `git status -s`
Expected: `app/models/referentiel.py`, `app/migration/versions/0010_add_manual_review_columns.py`, `tests/migration/test_migration.py`, `conception/2_ingestion/MLD_qualicheck.md`, `conception/annexes/MLD_qualicheck.md` — rien d'autre.

- [ ] **Step 11: Commit**

```bash
git add app/models/referentiel.py app/migration/versions/0010_add_manual_review_columns.py tests/migration/test_migration.py conception/2_ingestion/MLD_qualicheck.md conception/annexes/MLD_qualicheck.md
git commit -m "$(cat <<'EOF'
feat: add manual review columns to regle (migration 0010)

Ajoute reviewed_at, review_status, review_note — toutes nullables,
métadonnée de pipeline (même famille que les colonnes de provenance de
la spec E), renseignées manuellement après revue humaine des
classifications LLM. Aucun code du pipeline d'ingestion n'y touche
(conception/2_ingestion/G_revue_manuelle.md §2, §6).
EOF
)"
```

---

### Task 2: Validation finale — récapitulatif des critères

**Files:** aucun (tâche de vérification uniquement).

- [ ] **Step 1: Récapitulatif des critères de la spec (§6)**

Cocher chacun, déjà vérifié dans la Task 1 :

1. Migration 0010 up/down OK, aucune donnée existante perdue → Task 1 Steps 5-6
2. Les 3 colonnes existent, toutes nullables → Task 1 Step 5
3. `pytest`/`ruff` verts → Task 1 Step 9
4. Aucun code du pipeline ne référence ces colonnes → Task 1 Step 8

- [ ] **Step 2: Rapport final**

Confirmer à David que les 3 colonnes sont en place, prêtes à être renseignées
manuellement (`psql`) une fois qu'une première revue réelle aura lieu après le
chantier 3 (ré-ingestion réelle, spec/plan séparés).

---
