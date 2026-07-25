# Provenance des données et manifeste d'ingestion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendre traçable la provenance de chaque ligne `regle` (modèle LLM réellement utilisé, version de prompt, dates) via un manifeste d'ingestion versionné, sans plus jamais dupliquer une valeur de provenance entre le code et sa source.

**Architecture:** `app/ingestion/manifest.yml` (nouveau, commité) porte l'affectation rôle→modèle et la résolution vers la variable `.env` correspondante. `app/ingestion/prompts/enrich_rule.md` porte sa propre version en frontmatter. `app/ingestion/llm_client.py` lit les deux au démarrage et écrit les mêmes valeurs dans la provenance — structurellement impossible à désynchroniser. 4 colonnes nullables sur `regle` (migration Alembic 0009) ; `NULL` = ligne produite avant l'instrumentation.

**Tech Stack:** SQLAlchemy + Alembic (migration), Pydantic (schéma), PyYAML (nouvelle dépendance, parsing manifeste + frontmatter), pytest (tests existants à adapter + nouveaux tests ciblés).

**Spec source:** `conception/2_ingestion/E_provenance_manifeste.md` (validée, ne pas modifier son contenu dans ce plan — seul le code change).

## Global Constraints

- Toutes les nouvelles colonnes de `regle` sont **nullables** — `NULL` signifie "produite avant l'instrumentation" (spec §4, §8 critère 5). Ne jamais backfiller les 245 lignes existantes.
- `llm_model` contient le **nom logique** du manifeste (`kimi-k2.6`), jamais un nom de déploiement Azure (spec §4).
- **Une seule autorité par valeur** : aucune chaîne de modèle en dur ne doit subsister dans `app/` après ce chantier (spec §8 critère 4, vérifié par `grep -rn "kimi" app/`).
- `manifest.yml` ne contient **aucun secret** (secrets = `.env` uniquement) et **aucun historique interne** (l'historique, c'est `git log manifest.yml`) — spec §3.
- Nommage des colonnes : métier en français, technique en anglais (spec §7) — `llm_model`, `prompt_version`, `created_at`, `updated_at` sont tous des objets techniques, donc en anglais, cohérent avec `embedding`.
- Ne pas toucher au prompt V4 (chantier 2, hors périmètre) ni faire d'appel LLM réel facturé (chantier 3, hors périmètre) — spec §9.
- Retry logic existante (3 tentatives, backoff `tenacity`) inchangée par cet incrément.
- `ruff check` propre et `pytest` vert avant tout commit (`CLAUDE.md` racine du projet).
- Commits : titre en anglais, corps en français (`~/.claude/CLAUDE.md`).
- **Assumption explicite (à valider par David avant exécution)** : seule la variable `AZURE_DEPLOYMENT_INGESTION` est renommée en `AZURE_MODEL_KIMI` dans `.env`/`.env.example` — c'est la seule lue par du code réel (`grep` confirmé). Les 3 variables `AZURE_DEPLOYMENT_AUDIT_GENERATION`/`AZURE_DEPLOYMENT_AUDIT_DIALOGUE`/`AZURE_DEPLOYMENT_QUESTION_LIBRE` restent inchangées : elles ne sont lues par aucun code, US1/US2 n'étant pas conçus (spec §9, "manifeste pour US1/US2 à concevoir avec eux"). Idem, `AZURE_MODEL_GPT` de l'exemple spec §5.1 n'est **pas** ajouté : rien ne le lirait (YAGNI).
- **Gap identifié pendant la lecture de la spec, hors périmètre §5 mais causé par le renommage** : `conception/2_ingestion/ingestion.md:114` mentionne encore `llm_provider` en prose — corrigé au Tâche 9 par cohérence directe avec le renommage de cette tâche, pas une extension de périmètre.
- **Duplication pré-existante non résolue par ce plan** : `conception/annexes/MLD_qualicheck.md` et `conception/2_ingestion/MLD_qualicheck.md` sont actuellement des copies strictement identiques (`diff` confirmé). La Tâche 9 met à jour les deux pour ne pas les faire diverger, mais la question "laquelle est la source de vérité ?" reste ouverte — à signaler à David, pas à trancher silencieusement ici.

---

### Task 1: Dépendance PyYAML

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: le module `yaml` (PyYAML) disponible pour les tâches suivantes.

- [ ] **Step 1: Ajouter la dépendance**

Dans `pyproject.toml`, section `dependencies`, insérer `pyyaml` entre `python-dotenv` et `requests` (ordre alphabétique respecté) :

```toml
dependencies = [
    "alembic>=1.18.5",
    "beautifulsoup4>=4.12.2",
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "pgvector>=0.5.0",
    "psycopg2-binary>=2.9.12",
    "pydantic>=2.13.4",
    "python-dotenv>=1.2.2",
    "pyyaml>=6.0",
    "requests>=2.34.2",
    "sqlalchemy>=2.0.51",
    "tenacity>=8.2.0",
]
```

- [ ] **Step 2: Installer et vérifier**

Run: `uv sync && uv run python -c "import yaml; print(yaml.__version__)"`
Expected: affiche un numéro de version PyYAML, sans erreur.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
build: add PyYAML dependency

Nécessaire pour parser app/ingestion/manifest.yml et le frontmatter YAML
de enrich_rule.md (spec E, provenance des données).
EOF
)"
```

---

### Task 2: Manifeste d'ingestion + restructuration `.env`

**Files:**
- Create: `app/ingestion/manifest.yml`
- Modify: `.env.example`
- Modify: `.env` (local, non versionné)

**Interfaces:**
- Produces: fichier `app/ingestion/manifest.yml` lisible par `yaml.safe_load()`, structure `{"enrichissement": {"modele": str, "env_var": str}}`. Variable d'environnement `AZURE_MODEL_KIMI` (remplace `AZURE_DEPLOYMENT_INGESTION`).

- [ ] **Step 1: Créer `app/ingestion/manifest.yml`**

```yaml
# Décisions courantes du pipeline d'ingestion.
# Aucun historique ici : git s'en charge (git log manifest.yml).
# Aucun secret ici : voir .env.

enrichissement:
  modele: kimi-k2.6
  env_var: AZURE_MODEL_KIMI
```

- [ ] **Step 2: Modifier `.env.example`**

Remplacer la ligne `AZURE_DEPLOYMENT_INGESTION=...` (les 3 autres lignes `AZURE_DEPLOYMENT_AUDIT_*`/`QUESTION_LIBRE` restent inchangées, cf. Global Constraints) :

```bash
# LLM
AZURE_AI_ENDPOINT=...
AZURE_AI_API_KEY=...

AZURE_MODEL_KIMI=...      # nom de déploiement Azure — rôle résolu via app/ingestion/manifest.yml
AZURE_DEPLOYMENT_AUDIT_GENERATION=...   # gpt-5.4 — génération d'audit
AZURE_DEPLOYMENT_AUDIT_DIALOGUE=...     # gpt-5.4-mini — dialogue d'audit
AZURE_DEPLOYMENT_QUESTION_LIBRE=...     # gpt-5.4 — question libre
```

- [ ] **Step 3: Modifier `.env` local**

Dans le fichier `.env` local (non versionné), renommer la variable `AZURE_DEPLOYMENT_INGESTION` en `AZURE_MODEL_KIMI` en conservant sa valeur actuelle (le nom de déploiement Azure réel).

- [ ] **Step 4: Vérifier**

Run: `python3 -c "import yaml; d = yaml.safe_load(open('app/ingestion/manifest.yml')); assert d['enrichissement']['modele'] == 'kimi-k2.6'; assert d['enrichissement']['env_var'] == 'AZURE_MODEL_KIMI'; print('OK')"`
Expected: `OK`

Run: `grep -c "AZURE_DEPLOYMENT_INGESTION" .env.example`
Expected: `0` (plus aucune occurrence)

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/manifest.yml .env.example
git commit -m "$(cat <<'EOF'
feat: add ingestion manifest, restructure .env to model inventory

Le manifeste porte désormais l'affectation rôle → modèle
(enrichissement: kimi-k2.6, résolu via AZURE_MODEL_KIMI). Le .env ne
connaît plus que l'annuaire des déploiements joignables, plus les rôles
— une seule autorité par valeur (spec E §3-5.1-5.2).
EOF
)"
```

(`.env` local non commité — seul `.env.example` l'est.)

---

### Task 3: Frontmatter de version dans `enrich_rule.md`

**Files:**
- Modify: `app/ingestion/prompts/enrich_rule.md`

**Interfaces:**
- Produces: fichier commençant par un bloc frontmatter `---\nversion: 3\n---\n\n` avant le contenu existant.

- [ ] **Step 1: Ajouter le frontmatter**

En tête du fichier `app/ingestion/prompts/enrich_rule.md`, avant la ligne `# Enrichissement de Règles Opquast`, ajouter :

```yaml
---
version: 3
---

```

Le fichier commence donc par :

```markdown
---
version: 3
---

# Enrichissement de Règles Opquast

Tu es un expert en audit web et en qualité numérique. ...
```

La valeur reste `3` (contenu actuel du prompt, pas une intention — spec §5.3).

- [ ] **Step 2: Vérifier**

Run: `head -4 app/ingestion/prompts/enrich_rule.md`
Expected :
```
---
version: 3
---
```

- [ ] **Step 3: Commit**

```bash
git add app/ingestion/prompts/enrich_rule.md
git commit -m "$(cat <<'EOF'
docs: add version frontmatter to enrich_rule.md

La version du prompt n'existait nulle part dans la donnée. Le fichier
sait désormais ce qu'il est, même après un déplacement (spec E §5.3).
EOF
)"
```

---

### Task 4: Migration Alembic 0009 + modèle `Regle`

**Files:**
- Create: `app/migration/versions/0009_add_provenance_columns.py`
- Modify: `app/models/referentiel.py`
- Modify: `tests/migration/test_migration.py`

**Interfaces:**
- Consumes: aucune (couche BDD, base de toutes les tâches suivantes).
- Produces: colonnes `regle.llm_model` (String(64), nullable), `regle.prompt_version` (Integer, nullable), `regle.created_at` (DateTime, nullable), `regle.updated_at` (DateTime, nullable). Colonne `regle.llm_provider` n'existe plus.

- [ ] **Step 1: Écrire les tests d'intégration (doivent échouer avant la migration)**

Dans `tests/migration/test_migration.py`, après `test_colonnes_not_null_regle`, ajouter :

```python
def test_colonnes_provenance_regle(conn):
    """Les 4 colonnes de provenance doivent exister sur regle, toutes nullables."""
    colonnes = ["llm_model", "prompt_version", "created_at", "updated_at"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'regle'
            AND column_name = ANY(%s);
        """, (colonnes,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    manquantes = set(colonnes) - set(rows)
    assert not manquantes, f"Colonnes provenance manquantes : {manquantes}"
    non_nullable = [col for col in colonnes if rows.get(col) != "YES"]
    assert not non_nullable, f"Colonnes provenance incorrectement NOT NULL : {non_nullable}"


def test_colonne_llm_provider_absente(conn):
    """llm_provider doit avoir été renommée en llm_model (colonne absente)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'regle' AND column_name = 'llm_provider';
        """)
        count = cur.fetchone()[0]
    assert count == 0, "llm_provider encore présente — devrait être renommée llm_model"
```

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `make up && make migration && uv run pytest tests/migration/test_migration.py -v -k "provenance or llm_provider_absente"`
Expected: `test_colonnes_provenance_regle` FAIL (colonnes manquantes), `test_colonne_llm_provider_absente` PASS ou FAIL selon l'état — dans tous les cas, avant la migration 0009 la table n'a pas encore les 4 colonnes attendues.

- [ ] **Step 3: Modifier `app/models/referentiel.py`**

Remplacer la ligne `llm_provider = Column(String(20))` :

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, PrimaryKeyConstraint, String, Text
```

Dans la classe `Regle` :

```python
    llm_model = Column(String(64), nullable=True)
    prompt_version = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    embedding = Column(Vector(384))
```

(remplace la ligne `llm_provider = Column(String(20))` par les 4 lignes ci-dessus, juste avant `embedding`.)

- [ ] **Step 4: Créer la migration `0009_add_provenance_columns.py`**

```python
"""Rename llm_provider to llm_model, add prompt_version/created_at/updated_at

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regle",
        "llm_provider",
        existing_type=sa.String(20),
        type_=sa.String(64),
        existing_nullable=True,
    )
    op.alter_column(
        "regle",
        "llm_provider",
        new_column_name="llm_model",
        existing_type=sa.String(64),
    )
    op.add_column("regle", sa.Column("prompt_version", sa.Integer(), nullable=True))
    op.add_column("regle", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("regle", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("regle", "updated_at")
    op.drop_column("regle", "created_at")
    op.drop_column("regle", "prompt_version")
    op.alter_column(
        "regle",
        "llm_model",
        new_column_name="llm_provider",
        existing_type=sa.String(64),
    )
    op.alter_column(
        "regle",
        "llm_provider",
        existing_type=sa.String(64),
        type_=sa.String(20),
        existing_nullable=True,
    )
```

- [ ] **Step 5: Run pour vérifier le succès**

Run: `make migration && uv run pytest tests/migration/test_migration.py -v`
Expected: tous les tests PASS, y compris `test_colonnes_provenance_regle` et `test_colonne_llm_provider_absente`.

- [ ] **Step 6: Vérifier le downgrade (retester une migration from scratch)**

Run: `make downgrade && make migration && uv run pytest tests/migration/test_migration.py -v`
Expected: tous les tests PASS à nouveau (up/down/up symétrique, spec §8 critère 5).

- [ ] **Step 7: Vérification manuelle sur les données existantes (si la BDD contient déjà les 245 règles)**

Run: `make psql` puis dans la session psql :
```sql
SELECT COUNT(*) FROM regle WHERE prompt_version IS NULL AND created_at IS NULL;
```
Expected: retourne le nombre total de règles déjà en base (245 si l'ingestion précédente a eu lieu) — confirme qu'aucune reprise de données n'a eu lieu, conformément à spec §5.7/§8 critère 5.

- [ ] **Step 8: Commit**

```bash
git add app/models/referentiel.py app/migration/versions/0009_add_provenance_columns.py tests/migration/test_migration.py
git commit -m "$(cat <<'EOF'
feat: add provenance columns to regle (migration 0009)

Renomme llm_provider en llm_model (même nature, nom correct) et ajoute
prompt_version, created_at, updated_at — toutes nullables, NULL signifiant
"produit avant l'instrumentation" (spec E §4-§5.6-§5.7). Aucune reprise
des 245 lignes existantes.
EOF
)"
```

---

### Task 5: `EnrichedRule` — nouveaux champs de provenance

**Files:**
- Modify: `app/ingestion/schema.py`

**Interfaces:**
- Consumes: rien de nouveau (Pydantic pur).
- Produces: `EnrichedRule.llm_model: str | None = None`, `EnrichedRule.prompt_version: int | None = None` — noms et types que Task 6/7 consomment.

- [ ] **Step 1: Modifier `EnrichedRule`**

Dans `app/ingestion/schema.py`, remplacer :

```python
    strategie_source: str = "ia_import"
    llm_provider: str = "kimi-k2.6"
```

par :

```python
    strategie_source: str = "ia_import"
    llm_model: str | None = None
    prompt_version: int | None = None
```

(`strategie_source` garde son défaut — non concerné par le problème de provenance décrit en spec §1. `llm_provider="kimi-k2.6"` disparaît : c'était exactement la décoration dénoncée en spec §1 — plus aucun défaut de modèle en dur.)

- [ ] **Step 2: Vérifier qu'aucun test existant ne casse pour une mauvaise raison**

Run: `uv run pytest tests/unit/ingestion/test_aggregation.py tests/integration/ingestion/test_stockage_contexte.py -v`
Expected: tous PASS (ces tests n'instancient jamais `llm_provider` explicitement, donc insensibles au renommage). Les échecs attendus sont dans `test_enrichment.py` et `test_stockage.py`-like modules qui référencent `llm_provider` — traités en Task 6/7.

- [ ] **Step 3: Commit**

```bash
git add app/ingestion/schema.py
git commit -m "$(cat <<'EOF'
refactor: rename EnrichedRule.llm_provider to llm_model, add prompt_version

Suit le renommage de la colonne BDD (Task 4). Suppression du défaut en
dur "kimi-k2.6" : la valeur vient désormais du manifeste (spec E §5.5).
EOF
)"
```

---

### Task 6: `LLMClient` — lecture manifeste + frontmatter, suppression des valeurs en dur

**Files:**
- Modify: `app/ingestion/llm_client.py`
- Modify: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**
- Consumes: `EnrichedRule.llm_model`, `EnrichedRule.prompt_version` (Task 5).
- Produces: `load_manifest() -> dict`, `load_prompt_version() -> int | None` — fonctions module-level testables indépendamment. `LLMClient.model_name: str`, `LLMClient.prompt_version: int | None` — attributs lus par `enrich_single_rule()`.

- [ ] **Step 1: Écrire les tests (doivent échouer avant l'implémentation)**

Dans `tests/unit/ingestion/test_enrichment.py`, remplacer les deux assertions obsolètes et ajouter une classe de tests. D'abord, dans `test_enrich_single_rule_success`, remplacer :

```python
        assert enriched.strategie_source == "ia_import"
        assert enriched.llm_provider == "kimi-k2.6"
```

par :

```python
        assert enriched.strategie_source == "ia_import"
        assert enriched.llm_model == "kimi-k2.6"
        assert enriched.prompt_version == 3
```

Ensuite, ajouter en fin de fichier (après `TestLoadPromptContexte`) :

```python
class TestManifestAndPromptVersion:
    """Vérifie la lecture du manifeste et de la version de prompt."""

    def test_load_manifest_reads_enrichissement_role(self):
        from app.ingestion.llm_client import load_manifest

        manifest = load_manifest()

        assert manifest["enrichissement"]["modele"] == "kimi-k2.6"
        assert manifest["enrichissement"]["env_var"] == "AZURE_MODEL_KIMI"

    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 3

    def test_load_prompt_strips_frontmatter_from_llm_input(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_MODEL_KIMI", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
        )

        prompt = client.load_prompt(rule)

        assert "version: 3" not in prompt
        assert prompt.startswith("# Enrichissement de Règles Opquast")

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_llm_model_provenance_independent_of_env_var(self, mock_azure_llm, monkeypatch):
        """llm_model vient du manifeste, pas de la variable d'environnement résolue."""
        monkeypatch.setenv("AZURE_MODEL_KIMI", "un-nom-de-deploiement-quelconque")

        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance
        mock_response = MagicMock()
        mock_response.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Test", "guide_analyse": "Test"}'
        )
        mock_response.usage_metadata = {"input_tokens": 1, "output_tokens": 1}
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=1, number=1, intitule="Test", theme="Contenus",
            solution="S", controle="C", objectifs=["O"], tags=["T"],
            phases=["P"], slug="test",
        )

        enriched = client.enrich_single_rule(rule)

        assert enriched.llm_model == "kimi-k2.6"
        _, kwargs = mock_azure_llm.call_args
        assert kwargs["model"] == "un-nom-de-deploiement-quelconque"
```

Ajouter l'import manquant en tête de fichier (`test_enrichment.py`) si absent :

```python
from unittest.mock import MagicMock, patch
```

(déjà présent — vérifier qu'il n'y a pas de doublon d'import.)

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: FAIL sur `test_enrich_single_rule_success` (`AttributeError: llm_model`), `ImportError: cannot import name 'load_manifest'`, etc.

- [ ] **Step 3: Implémenter dans `app/ingestion/llm_client.py`**

Ajouter l'import en tête de fichier :

```python
import yaml
```

Ajouter deux fonctions module-level, après `PROMPT_PLACEHOLDERS` et avant `class EnrichmentOutput` :

```python
def load_manifest() -> dict:
    """Charge les décisions courantes du pipeline (app/ingestion/manifest.yml)."""
    manifest_path = Path(__file__).parent / "manifest.yml"
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _read_prompt_file() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "enrich_rule.md"
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()


def load_prompt_version() -> int | None:
    """Lit la version du prompt depuis le frontmatter de enrich_rule.md."""
    text = _read_prompt_file()
    if not text.startswith("---\n"):
        return None
    _, frontmatter_raw, _ = text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_raw) or {}
    return frontmatter.get("version")
```

Modifier `LLMClient.__init__` :

```python
    def __init__(self):
        """Initialise le client Azure OpenAI et le parser JSON."""
        manifest = load_manifest()
        role = manifest["enrichissement"]
        self.model_name = role["modele"]
        self.prompt_version = load_prompt_version()

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
        )
        self.parser = JsonOutputParser(pydantic_object=EnrichmentOutput)
        self.input_tokens = 0
        self.output_tokens = 0
```

Modifier `load_prompt()` pour retirer le frontmatter avant substitution des placeholders :

```python
    def load_prompt(self, rule: Rule) -> str:
        """
        Charge le prompt depuis prompts/enrich_rule.md et remplace les placeholders.

        Remplacement manuel (pas de str.format()) car le prompt contient des
        accolades JSON littérales dans les exemples few-shot, qui entreraient
        en conflit avec la syntaxe de formatage de PromptTemplate.
        """
        prompt_text = _read_prompt_file()
        if prompt_text.startswith("---\n"):
            _, _, prompt_text = prompt_text.split("---", 2)
            prompt_text = prompt_text.lstrip("\n")

        values = {
            "intitule": rule.intitule,
            "contexte": rule.contexte or "(non disponible)",
            "solution": rule.solution,
            "controle": rule.controle,
            "objectifs": ", ".join(rule.objectifs),
            "tags": ", ".join(rule.tags),
            "phases": ", ".join(rule.phases),
        }
        for placeholder in PROMPT_PLACEHOLDERS:
            prompt_text = prompt_text.replace(f"{{{placeholder}}}", values[placeholder])

        return prompt_text
```

Modifier la fin de `enrich_single_rule()` :

```python
        return EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
            theme=rule.theme,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=rule.objectifs,
            tags=rule.tags,
            phases=rule.phases,
            slug=rule.slug,
            strategie_analyse=parsed["strategie_analyse"],
            strategie_justification=parsed["strategie_justification"],
            guide_analyse=parsed["guide_analyse"],
            strategie_source="ia_import",
            llm_model=self.model_name,
            prompt_version=self.prompt_version,
        )
```

- [ ] **Step 4: Mettre à jour les 2 tests existants qui référencent `AZURE_DEPLOYMENT_INGESTION`**

Dans `TestLoadPromptContexte` (`test_load_prompt_includes_contexte_when_present`, `test_load_prompt_handles_missing_contexte`), remplacer :

```python
        monkeypatch.setenv("AZURE_DEPLOYMENT_INGESTION", "test-model")
```

par :

```python
        monkeypatch.setenv("AZURE_MODEL_KIMI", "test-model")
```

(2 occurrences.)

- [ ] **Step 5: Run pour vérifier le succès**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: tous PASS.

- [ ] **Step 6: Vérifier l'absence de valeur en dur**

Run: `grep -rn "kimi" app/*.py app/**/*.py 2>/dev/null | grep -v manifest.yml`
Expected: aucune occurrence dans du code `.py` (spec §8 critère 4). Seule occurrence légitime : `app/ingestion/manifest.yml` (fichier YAML, pas `.py`).

- [ ] **Step 7: Commit**

```bash
git add app/ingestion/llm_client.py tests/unit/ingestion/test_enrichment.py
git commit -m "$(cat <<'EOF'
feat: read model and prompt version from manifest, drop hardcoded values

llm_client.py lit désormais app/ingestion/manifest.yml (modèle + variable
d'env à résoudre) et le frontmatter de enrich_rule.md (version). La
provenance écrite utilise structurellement les mêmes valeurs que celles
ayant servi à l'appel LLM (spec E §5.4).
EOF
)"
```

---

### Task 7: Stockage — persister et relire la provenance

**Files:**
- Modify: `app/ingestion/stockage.py`
- Create: `tests/integration/ingestion/test_stockage_provenance.py`

**Interfaces:**
- Consumes: `EnrichedRule.llm_model`, `EnrichedRule.prompt_version` (Task 5) ; `Regle.llm_model`, `Regle.prompt_version`, `Regle.created_at`, `Regle.updated_at` (Task 4).
- Produces: `upsert_rule()` renseigne les 4 colonnes ; `load_enriched_rules_from_db()` relit `llm_model`/`prompt_version`.

- [ ] **Step 1: Écrire le test d'intégration (doit échouer avant l'implémentation)**

Créer `tests/integration/ingestion/test_stockage_provenance.py` :

```python
"""
Test d'intégration : provenance (llm_model, prompt_version, created_at,
updated_at) via upsert_rule + load_enriched_rules_from_db. Nécessite les
conteneurs Docker démarrés et la migration 0009 appliquée.
"""
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.schema import EnrichedRule
from app.models.referentiel import Regle
from app.ingestion.stockage import clear_opquast_tables, load_enriched_rules_from_db, store_rules

load_dotenv()


def _database_url():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_provenance_round_trip(session):
    """llm_model et prompt_version survivent à un cycle store -> load."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle avec provenance", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].llm_model == "kimi-k2.6"
    assert by_number[1].prompt_version == 3

    clear_opquast_tables(session)


def test_created_at_set_once_updated_at_changes_on_reupsert(session):
    """created_at ne change pas lors d'un ré-upsert ; updated_at change."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle initiale", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule]))
    first = session.query(Regle).filter_by(numero=1).one()
    created_at_initial = first.created_at
    updated_at_initial = first.updated_at
    session.expunge(first)

    rule_v2 = EnrichedRule(
        id=1, number=1, intitule="Règle modifiée", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution modifiée", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule_v2]))
    second = session.query(Regle).filter_by(numero=1).one()

    assert second.created_at == created_at_initial
    assert second.updated_at >= updated_at_initial

    clear_opquast_tables(session)
```

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `make up && make migration && uv run pytest tests/integration/ingestion/test_stockage_provenance.py -v`
Expected: FAIL (`upsert_rule` ne renseigne pas encore `llm_model`/`prompt_version`/`created_at`/`updated_at`).

- [ ] **Step 3: Implémenter dans `app/ingestion/stockage.py`**

Ajouter l'import en tête de fichier :

```python
from datetime import UTC, datetime
```

Modifier `upsert_rule()` :

```python
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
    theme = get_or_create(session, Theme, theme=enriched_rule.theme)

    now = datetime.now(UTC).replace(tzinfo=None)

    if regle is None:
        regle = Regle(numero=enriched_rule.number, created_at=now)
        session.add(regle)

    regle.theme_id = theme.id

    regle.intitule = enriched_rule.intitule
    regle.contexte = enriched_rule.contexte
    regle.solution = enriched_rule.solution
    regle.controle = enriched_rule.controle
    regle.strategie_analyse = enriched_rule.strategie_analyse
    regle.strategie_justification = enriched_rule.strategie_justification
    regle.strategie_source = enriched_rule.strategie_source
    regle.guide_analyse = enriched_rule.guide_analyse
    regle.llm_model = enriched_rule.llm_model
    regle.prompt_version = enriched_rule.prompt_version
    regle.updated_at = now

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

Modifier `load_enriched_rules_from_db()` — remplacer les deux dernières lignes de la construction `EnrichedRule(...)` :

```python
            strategie_source=regle.strategie_source,
            llm_model=regle.llm_model,
            prompt_version=regle.prompt_version,
        )
```

- [ ] **Step 4: Run pour vérifier le succès**

Run: `uv run pytest tests/integration/ingestion/test_stockage_provenance.py tests/integration/ingestion/test_stockage_contexte.py -v`
Expected: tous PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/stockage.py tests/integration/ingestion/test_stockage_provenance.py
git commit -m "$(cat <<'EOF'
feat: persist and reload provenance columns in stockage

upsert_rule() renseigne created_at (à la création uniquement),
updated_at (à chaque upsert), llm_model et prompt_version.
load_enriched_rules_from_db() les relit pour le hook --resume
(spec E §5.8).
EOF
)"
```

---

### Task 8: `scripts/ingestion_test.py` — bouchon aligné sur le nouveau schéma

**Files:**
- Modify: `scripts/ingestion_test.py`

**Interfaces:**
- Consumes: `EnrichedRule.llm_model`, `EnrichedRule.prompt_version` (Task 5).

- [ ] **Step 1: Modifier `create_enriched_rule_stub()`**

Remplacer :

```python
        strategie_source="ia_import",
        llm_provider="test",
    )
```

par :

```python
        strategie_source="ia_import",
        llm_model="test",
        prompt_version=0,  # 0 = bouchon, pas un vrai numéro de version de prompt
    )
```

- [ ] **Step 2: Vérifier par exécution réelle**

Run: `make up && make migration && uv run python scripts/ingestion_test.py`
Expected: le script se termine sans erreur, "✓ Ingestion complète réussie" dans les logs.

Puis : `make psql` et dans la session :
```sql
SELECT llm_model, prompt_version, created_at, updated_at FROM regle LIMIT 3;
```
Expected: les 4 colonnes sont renseignées (`llm_model='test'`, `prompt_version=0`, dates non nulles) — spec §8 critère 6.

- [ ] **Step 3: Commit**

```bash
git add scripts/ingestion_test.py
git commit -m "$(cat <<'EOF'
fix: align ingestion_test.py stub with llm_model/prompt_version rename

Le bouchon d'enrichissement doit renseigner les 4 colonnes de provenance
pour rester une validation de schéma représentative (spec E §8 critère 6).
EOF
)"
```

---

### Task 9: Visibilité du coût sur échec de stockage (§5.10) + documentation

**Files:**
- Modify: `scripts/ingestion.py`
- Modify: `conception/2_ingestion/MLD_qualicheck.md`
- Modify: `conception/annexes/MLD_qualicheck.md`
- Modify: `conception/2_ingestion/ingestion.md`

**Interfaces:**
- Aucune (dernière tâche fonctionnelle + tâche documentaire, pas de nouvelle interface consommée ailleurs).

- [ ] **Step 1: Déplacer le calcul de coût avant l'Étape 4 dans `scripts/ingestion.py`**

Dans la fonction `main()`, section `else` (pipeline complet), retirer le bloc de calcul de coût qui suit actuellement le bloc `Étape 4 — Stockage`, et l'insérer **avant** ce bloc, juste après `logger.info("Étape 3 — Enrichissement : terminée")` :

```python
        try:
            logger.info("Étape 3 — Enrichissement : démarrage")
            progress_logger.info("Étape 3 — Enrichissement : démarrage")
            enriched = enrich_rules(rules)
            logger.info("Étape 3 — Enrichissement : terminée")
        except Exception as e:
            logger.error("Étape 3 — Enrichissement : ÉCHEC (%s)", e)
            sys.exit(1)

        price_input_per_1m = float(os.getenv("KIMI_PRICE_INPUT_PER_1M", "0"))
        price_output_per_1m = float(os.getenv("KIMI_PRICE_OUTPUT_PER_1M", "0"))
        cost = (
            enriched.input_tokens * price_input_per_1m
            + enriched.output_tokens * price_output_per_1m
        ) / 1_000_000

        summary = (
            f"Tokens — entrée : {enriched.input_tokens}, sortie : {enriched.output_tokens}, "
            f"total : {enriched.input_tokens + enriched.output_tokens}, "
            f"coût estimé : {cost:.4f} €"
        )
        logger.info(summary)
        progress_logger.info(summary)

        try:
            logger.info("Étape 4 — Stockage : démarrage")
            progress_logger.info("Étape 4 — Stockage : démarrage")
            with Session(engine) as session:
                store_rules(session, enriched)
            logger.info("Étape 4 — Stockage : terminée")
        except Exception as e:
            logger.error("Étape 4 — Stockage : ÉCHEC (%s)", e)
            sys.exit(1)
```

(Supprimer l'ancien bloc de calcul de coût qui se trouvait après le `try/except` de l'Étape 4 — il ne doit plus y en avoir qu'un seul exemplaire, avant l'Étape 4.)

- [ ] **Step 2: Vérifier manuellement le correctif**

Provoquer un échec de stockage contrôlé : temporairement, dans un test manuel, faire échouer `store_rules` (par ex. couper la connexion BDD ou utiliser `--limit 1` avec une valeur de test invalide), et vérifier dans `logs/ingestion.log` que la ligne `Tokens — entrée : ..., coût estimé : ...` apparaît **avant** la ligne `Étape 4 — Stockage : ÉCHEC`, donc que le coût est bien journalisé malgré l'échec (spec §8 critère 8). Restaurer l'état normal ensuite.

- [ ] **Step 3: Documenter les 4 colonnes de provenance dans le MLD**

Dans `conception/2_ingestion/MLD_qualicheck.md`, section `### regle`, remplacer :

```
  llm_provider *          VARCHAR(20)
```

par :

```
  llm_model *             VARCHAR(64)     -- nom logique du modèle (manifest.yml), pas un nom de déploiement
  prompt_version *        INT                       -- version du prompt (frontmatter enrich_rule.md)
  created_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
  updated_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
```

Ajouter, après le bloc `regle`, un court paragraphe :

```markdown
**Règle de nommage des colonnes** : le vocabulaire du domaine reste en français,
le vocabulaire technique en anglais (principe de langage omniprésent, DDD). Test :
un auditeur qualité prononcerait-il ce mot en parlant de son métier ? Détail :
`conception/2_ingestion/E_provenance_manifeste.md` §7.
```

Appliquer le même changement dans `conception/annexes/MLD_qualicheck.md` (copie actuellement identique — cf. Global Constraints).

- [ ] **Step 4: Corriger la mention `llm_provider` dans `ingestion.md`**

Dans `conception/2_ingestion/ingestion.md:114`, remplacer `llm_provider` par `llm_model` dans la phrase existante (pas de reformulation, seul le nom de champ change).

- [ ] **Step 5: Commit**

```bash
git add scripts/ingestion.py conception/2_ingestion/MLD_qualicheck.md conception/annexes/MLD_qualicheck.md conception/2_ingestion/ingestion.md
git commit -m "$(cat <<'EOF'
fix: log token cost before storage step, not after

Un run qui échoue au stockage journalisait son coût nulle part (perte
constatée le 19/07 : ~6€ de tokens facturés jamais journalisés). Le
calcul de coût utilise déjà enriched.input_tokens/output_tokens,
disponibles dès l'Étape 3 (spec E §1 quatrième manque, §5.10).

Documente aussi les 4 colonnes de provenance dans le MLD et corrige la
dernière mention de llm_provider dans ingestion.md.
EOF
)"
```

---

### Task 10: Validation finale — critères de la spec

**Files:** aucun (tâche de vérification uniquement).

- [ ] **Step 1: Suite de tests complète**

Run: `make test`
Expected: tous les tests PASS (unitaires + intégration + migration).

- [ ] **Step 2: Lint**

Run: `uv run ruff check .`
Expected: aucune erreur (spec §8 critère 7).

- [ ] **Step 3: Grep de non-régression**

Run: `grep -rn "llm_provider" app/ scripts/ tests/`
Expected: aucune occurrence (toutes renommées en `llm_model`).

Run: `grep -rn "kimi" app/*.py app/**/*.py scripts/*.py 2>/dev/null`
Expected: aucune occurrence (spec §8 critère 4) — seule `app/ingestion/manifest.yml` (non `.py`) porte la valeur.

- [ ] **Step 4: Récapitulatif des 8 critères de la spec (§8)**

Cocher chacun en le reliant à la tâche qui le couvre :

1. `manifest.yml` lu par le code → Task 6 (`load_manifest()`, test `test_load_manifest_reads_enrichissement_role`)
2. `.env` change le déploiement sans changer `llm_model` → Task 6 (`test_llm_model_provenance_independent_of_env_var`)
3. Frontmatter change `prompt_version` → Task 6 (`test_load_prompt_version_reads_frontmatter`)
4. Aucune chaîne de modèle en dur → Task 10 Step 3 (grep)
5. Migration 0009 up/down OK, 245 lignes à `NULL` → Task 4 (Steps 5-7)
6. Ingestion de test renseigne les 4 colonnes → Task 8 (Step 2)
7. `pytest` vert, `ruff` propre → Task 10 (Steps 1-2)
8. Coût journalisé malgré échec de stockage → Task 9 (Step 2)

- [ ] **Step 5: Rapport final**

Confirmer à David que les 8 critères sont vérifiés avant de considérer la spec E comme livrée et de passer au chantier 2 (prompt V4).

---
