# Isolation des tests d'intégration destructeurs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empêcher les tests d'intégration `test_stockage_contexte.py` et
`test_stockage_provenance.py` de jamais écraser la vraie base de dev locale
(`qualicheck`), en les faisant pointer obligatoirement vers une base de test
dédiée (`qualicheck_test`), créée et migrée séparément.

**Architecture:** Une nouvelle variable d'environnement obligatoire,
`POSTGRES_TEST_DB`, distincte de `POSTGRES_DB`. Une nouvelle cible Makefile
(`migration-test`) crée cette base si absente et la migre. Les deux tests
concernés lisent `POSTGRES_TEST_DB` via `os.environ[...]` (pas de valeur par
défaut) — son absence doit faire échouer le test immédiatement, jamais un
repli silencieux vers `POSTGRES_DB`. Le CI reçoit la même variable (valeur =
`POSTGRES_DB`, sa base éphémère étant déjà jetable), donc son comportement ne
change pas.

**Tech Stack:** Postgres (conteneur `qualicheck-postgres` existant, docker
compose), Alembic (`scripts/migration.py`), pytest, GitHub Actions.

## Global Constraints

- Aucune nouvelle base de données ni nouveau service Docker — `qualicheck_test`
  vit sur le conteneur Postgres existant.
- `POSTGRES_TEST_DB` doit être **obligatoire** côté test (`os.environ["POSTGRES_TEST_DB"]`)
  — jamais de fallback implicite vers `POSTGRES_DB`.
- `.env` réel de David contient déjà des secrets (`POSTGRES_PASSWORD`, etc.) —
  toute modification de `.env` doit être un **ajout de ligne**, jamais une
  réécriture du fichier.
- Le CI ne doit nécessiter aucun nouveau secret GitHub — réutiliser
  `secrets.POSTGRES_DB` pour `POSTGRES_TEST_DB`.
- Spec source : `docs/superpowers/specs/2026-07-25-isolation-tests-integration-bdd.md`
  (commit `f7dad74`) — texte et code déjà validés, à reprendre verbatim.
- Pas de nouvelle branche : travail sur `feature`, dans la continuité des
  chantiers précédents (D, E, F, G, H).

---

### Task 1: Provisionner la base de test (`qualicheck_test`)

**Files:**

- Modify: `.env` (ajout de ligne, pas de réécriture)
- Modify: `.env.example`
- Modify: `Makefile:1` (ligne `.PHONY`), `Makefile:34-36` (nouvelle cible
  après la cible `psql`)

**Interfaces:**

- Consumes: rien (première tâche).
- Produces: variable d'environnement `POSTGRES_TEST_DB` (valeur locale :
  `qualicheck_test`) ; cible Makefile `migration-test` — une base Postgres
  `qualicheck_test` existante et migrée au schéma courant (alembic head
  `0010`), consommée par la Task 2.

- [ ] **Step 1: Ajouter `POSTGRES_TEST_DB` à `.env`**

Le fichier `.env` réel contient déjà (entre autres) :

```text
POSTGRES_USER=qualicheck
POSTGRES_PASSWORD=<secret existant>
POSTGRES_DB=qualicheck
POSTGRES_HOST=localhost
POSTGRES_PORT=8832
```

Ajouter une ligne juste après `POSTGRES_PORT=8832` (ne toucher à aucune
autre ligne du fichier) :

```text
POSTGRES_TEST_DB=qualicheck_test
```

- [ ] **Step 2: Documenter la variable dans `.env.example`**

Dans `.env.example`, le bloc `# Connexion PostgreSQL` est :

```text
# Connexion PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=
POSTGRES_PORT=
```

Remplacer par :

```text
# Connexion PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=
POSTGRES_PORT=

# Base de test dédiée aux tests d'intégration destructeurs — jamais
# POSTGRES_DB (voir CLAUDE.md, incident du 2026-07-25)
POSTGRES_TEST_DB=
```

- [ ] **Step 3: Ajouter la cible `migration-test` au Makefile**

Le `Makefile` actuel a cette ligne `.PHONY` en tête :

```makefile
.PHONY: up down migration downgrade ingestion clear psql test
```

Remplacer par :

```makefile
.PHONY: up down migration downgrade ingestion clear psql test migration-test
```

Puis, juste après la cible `psql` existante (avant `## Lance les tests
d'intégration...`), insérer :

```makefile
## Crée (si absente) et migre la base de test dédiée aux tests d'intégration
## destructeurs (jamais la base de dev réelle)
migration-test:
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d postgres -tc \
		"SELECT 1 FROM pg_database WHERE datname = '$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)'" | grep -q 1 || \
		docker exec qualicheck-postgres createdb -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" "$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)"
	POSTGRES_DB="$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)" uv run python scripts/migration.py
```

(Les lignes de recette Makefile sont indentées par une tabulation, pas des
espaces — respecter l'indentation des cibles voisines.)

- [ ] **Step 4: Exécuter la cible et vérifier la création + migration**

Run: `make migration-test`

Expected: la base `qualicheck_test` est créée (ou déjà présente) puis
`alembic upgrade head` s'exécute dessus sans erreur.

Vérifier ensuite :

```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck_test -c "\dt"
```

Expected: les mêmes tables que sur `qualicheck` (dont `regle`,
`alembic_version`).

- [ ] **Step 5: Commit**

```bash
git add .env.example Makefile
git commit -m "$(cat <<'EOF'
feat: add dedicated test database provisioning

Nouvelle cible make migration-test + variable POSTGRES_TEST_DB
(.env.example) pour isoler les tests d'intégration destructeurs de la
vraie base de dev locale.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(Le fichier `.env` réel n'est pas versionné — rien à committer dessus.)

---

### Task 2: Faire pointer les tests concernés vers `POSTGRES_TEST_DB`

**Files:**

- Modify: `tests/integration/ingestion/test_stockage_contexte.py:20-26`
- Modify: `tests/integration/ingestion/test_stockage_provenance.py:21-27`

**Interfaces:**

- Consumes: base `qualicheck_test` migrée (Task 1, Step 4) ; variable
  `POSTGRES_TEST_DB` dans `.env` (Task 1, Step 1).
- Produces: les deux fichiers de test n'ouvrent plus jamais de connexion
  vers `POSTGRES_DB` — consommé par la vérification finale (Task 4).

- [ ] **Step 1: Modifier `_database_url()` dans `test_stockage_contexte.py`**

Remplacer :

```python
def _database_url():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
```

par :

```python
def _database_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
```

- [ ] **Step 2: Modifier `_database_url()` dans `test_stockage_provenance.py`**

Même remplacement (fonction identique dans les deux fichiers) :

Remplacer :

```python
def _database_url():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
```

par :

```python
def _database_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
```

- [ ] **Step 3: Noter le nombre de lignes réel de `regle` avant test**

Run:

```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc "SELECT count(*) FROM regle;"
```

Noter la valeur affichée (au moment d'écrire ce plan : `0`, la table étant
vide suite à l'incident du 2026-07-25 — la valeur peut différer si une
ré-ingestion a eu lieu entre-temps).

- [ ] **Step 4: Lancer les deux tests et vérifier qu'ils passent**

Run:

```bash
set -a && source .env && set +a
uv run pytest tests/integration/ingestion/test_stockage_contexte.py tests/integration/ingestion/test_stockage_provenance.py -v
```

Expected: `3 passed` (`test_contexte_round_trip`,
`test_provenance_round_trip`, `test_created_at_set_once_updated_at_changes_on_reupsert`).

- [ ] **Step 5: Vérifier que la vraie base `qualicheck` n'a pas bougé**

Run:

```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc "SELECT count(*) FROM regle;"
```

Expected: exactement la même valeur qu'au Step 3 (0, ou la valeur notée) —
preuve que les tests n'ont plus touché à `qualicheck`.

- [ ] **Step 6: Vérifier l'échec explicite si `POSTGRES_TEST_DB` est absente**

Run:

```bash
set -a && source .env && set +a
unset POSTGRES_TEST_DB
uv run pytest tests/integration/ingestion/test_stockage_provenance.py -v
```

Expected: `FAILED` avec `KeyError: 'POSTGRES_TEST_DB'` (pas un fallback
silencieux, pas un test qui passe en silence contre `qualicheck`).

- [ ] **Step 7: Commit**

```bash
git add tests/integration/ingestion/test_stockage_contexte.py tests/integration/ingestion/test_stockage_provenance.py
git commit -m "$(cat <<'EOF'
fix: point destructive integration tests at dedicated test database

test_stockage_contexte.py et test_stockage_provenance.py utilisaient
POSTGRES_DB (la vraie base de dev locale) pour clear_opquast_tables() en
setup/teardown. Bascule vers POSTGRES_TEST_DB, obligatoire (pas de
fallback), suite à la perte de la ré-ingestion V5 le 2026-07-25.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Mettre à jour le CI

**Files:**

- Modify: `.github/workflows/ci-feature.yml:29-34` (bloc `env` du job)

**Interfaces:**

- Consumes: rien de nouveau côté CI (le secret `POSTGRES_DB` existe déjà).
- Produces: le job CI expose `POSTGRES_TEST_DB` aux étapes de test, avec la
  même valeur que `POSTGRES_DB` — consommé par les deux tests modifiés en
  Task 2 lors de leur exécution en CI.

- [ ] **Step 1: Ajouter `POSTGRES_TEST_DB` au bloc `env` du job**

Remplacer :

```yaml
    env:
      POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
      POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
      POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
      POSTGRES_HOST: localhost
      POSTGRES_PORT: 5432
```

par :

```yaml
    env:
      POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
      POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
      POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
      POSTGRES_TEST_DB: ${{ secrets.POSTGRES_DB }}
      POSTGRES_HOST: localhost
      POSTGRES_PORT: 5432
```

Ne pas toucher au bloc `services.postgres.env` (lignes 17-20) — ce bloc
configure uniquement le conteneur de service, pas les variables lues par
les tests.

- [ ] **Step 2: Vérifier la syntaxe YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci-feature.yml'))"`

Expected: aucune erreur.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci-feature.yml
git commit -m "$(cat <<'EOF'
ci: expose POSTGRES_TEST_DB for destructive integration tests

Même valeur que POSTGRES_DB — la base éphémère du CI est déjà jetable,
donc aucun changement de comportement, seulement la variable requise
désormais par test_stockage_contexte.py et test_stockage_provenance.py.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(La vérification réelle du comportement CI se fera au prochain push,
déclenché par David — pas dans ce plan.)

---

### Task 4: Documenter la convention + vérification finale

**Files:**

- Modify: `CLAUDE.md:126-129` (section « Principes généraux (tout le
  projet) »)

**Interfaces:**

- Consumes: rien de nouveau.
- Produces: convention documentée, consultable par tout futur chantier
  ajoutant un test d'intégration touchant Postgres.

- [ ] **Step 1: Ajouter la convention dans `CLAUDE.md`**

La section actuelle (lignes 126-129) est :

```markdown
## Principes généraux (tout le projet)

- **Retry LLM** : 3 tentatives avec backoff croissant sur tout appel LLM, avant de considérer l'appel en échec définitif.
```

Remplacer par :

```markdown
## Principes généraux (tout le projet)

- **Retry LLM** : 3 tentatives avec backoff croissant sur tout appel LLM, avant de considérer l'appel en échec définitif.
- **Tests d'intégration Postgres** : tout test nécessitant une vraie connexion Postgres doit utiliser `POSTGRES_TEST_DB` (base dédiée `qualicheck_test`, provisionnée via `make migration-test`), jamais `POSTGRES_DB` directement. Suite à l'incident du 2026-07-25 : un `pytest tests/` lancé juste après une ré-ingestion réelle (245 règles, 4,32 €) a effacé ces données via un test d'intégration qui vidait la vraie base de dev locale.
```

- [ ] **Step 2: Lancer la suite complète de tests**

Run: `uv run pytest tests/ -v`

Expected: tous les tests passent (le nombre exact dépend de l'état du
dépôt au moment de l'exécution — vérifier qu'il n'y a aucun `FAILED`).

- [ ] **Step 3: Lancer ruff**

Run: `uv run ruff check`

Expected: `All checks passed!`

- [ ] **Step 4: Vérifier une dernière fois l'intégrité de `qualicheck`**

Run:

```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck -tc "SELECT count(*) FROM regle;"
```

Expected: valeur inchangée par rapport à la Task 2, Step 3/5 — la suite
complète (y compris `tests/migration/`) n'a pas touché à `qualicheck`.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: document POSTGRES_TEST_DB convention for integration tests

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Fin de plan

Après la Task 4, utiliser superpowers:finishing-a-development-branch — pas
de nouvelle branche à créer (travail resté sur `feature`, comme les
chantiers D à H). Pas de ré-ingestion réelle dans ce plan : la
reconstitution des 245 règles V5 perdues reste une décision et une action
de David, hors périmètre (voir spec §5).
