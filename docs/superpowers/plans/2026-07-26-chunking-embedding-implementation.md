# Chunking, Embedding, Indexation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter les Étapes 5-7 du pipeline (chunking, embedding,
indexation) : `regle.embedding` passe de `vector(384)` (jamais utilisé) à
`vector(1536)`, un module de construction de chunk, un client d'embedding
Azure, et deux points d'entrée (backfill indépendant + intégration au
pipeline complet).

**Architecture:** `app/ingestion/chunking.py` construit le texte structuré
d'un chunk depuis les champs d'une règle. `app/ingestion/embedding.py`
porte un client dédié (`openai` brut, pas `langchain` — nécessaire pour
lire les tokens consommés dans la réponse, absents de l'interface
`Embeddings` de langchain) qui calcule les vecteurs par lots de 50.
`scripts/embed_rules.py` (nouveau, sur le modèle d'`enrich_again.py`)
recalcule l'embedding des 245 lignes déjà en base. `scripts/ingestion.py`
gagne une Étape 6 pour les futures ré-ingestions complètes.

**Tech Stack:** Python, SQLAlchemy, Pydantic, `openai` (client brut),
`tenacity` (retry), pgvector, Alembic, pytest.

## Global Constraints

- Spec source : `conception/2_ingestion/L_chunking_embedding_indexation.md`
  (validée, commit `e6d9d9d`) — toute valeur exacte de ce plan en est
  extraite verbatim.
- **"1 règle = 1 chunk"** — non négociable (justifié dans la spec §3 et
  `conception/2_ingestion/ingestion.md` §Étape 5).
- Contenu du chunk : `intitulé + contexte + solution + controle + guide_analyse + tags + phases`,
  structuré avec labels, `contexte` omis proprement si `None`.
- **Dimension du vecteur : 1536, native, passée explicitement**
  (`dimensions=1536` dans chaque appel API) — **jamais 384**. Cette valeur
  a été explicitement débattue et tranchée avec David ; ne pas revenir à
  384 par réflexe d'économie ou de cohérence avec l'ancien schéma.
- Migration de schéma faite **maintenant** (pas différée) : aucune donnée
  réelle n'existe sur `regle.embedding` (`NULL` partout).
- Batch de 50 règles par appel API. Retry : `@retry` `tenacity` (3
  tentatives, backoff exponentiel 2/4/8s) — même decorator que
  `enrich_single_rule()` dans `app/ingestion/llm_client.py`, appliqué au
  niveau du lot (une panne ne retente que son propre lot de 50).
- **Pas de re-embedding automatique** depuis `upsert_rule()`/`enrich_again()`
  — hors périmètre de ce plan.
- `scripts/embed_rules.py` recalcule l'embedding de **toutes** les règles
  à chaque exécution (pas seulement celles à `NULL`).
- `manifest.yml` : prix en **euros**, tarif public converti par estimation
  (`0.0184` €/M tokens), à corriger dès qu'une vraie facture existe.
- **Aucune tâche de ce plan ne doit exécuter `scripts/embed_rules.py`,
  `scripts/ingestion.py`, ni aucun appel réel à l'API Azure embeddings.**
  Toute vérification se fait via tests automatisés avec mocks (aucun test
  ne doit faire de requête réseau réelle) et via `qualicheck_test` pour les
  tests d'intégration/migration nécessitant une vraie connexion Postgres —
  jamais `qualicheck` en écriture. Le premier calcul réel reste une
  décision et une action de David, hors périmètre de ce plan.
- Pas de nouvelle branche : travail sur `feature`, dans la continuité des
  chantiers D à L.
- Hors périmètre (spec §6, ne pas implémenter) : migration vers
  Infomaniak, re-embedding automatique, US2, `--dry-run`/confirmation
  interactive sur `scripts/embed_rules.py`.

---

### Task 1 : Migration 0011 — élargir `regle.embedding` à `vector(1536)`

**Files:**

- Create: `app/migration/versions/0011_widen_embedding_dimension.py`
- Modify: `app/models/referentiel.py:45`
- Test: `tests/migration/test_migration.py` (nouvelle fonction)

**Interfaces:**

- Consumes : rien (première tâche).
- Produces : colonne `regle.embedding` en `vector(1536)`, index HNSW
  `regle_embedding_idx` recréé sur cette nouvelle dimension — consommé par
  la Task 4 (écriture de l'embedding via `upsert_rule()`).

- [ ] **Step 1 : Créer la migration**

Créer `app/migration/versions/0011_widen_embedding_dimension.py` :

```python
"""Élargit regle.embedding de vector(384) à vector(1536)

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-26
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(384)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")
```

- [ ] **Step 2 : Mettre à jour le modèle SQLAlchemy**

Dans `app/models/referentiel.py`, remplacer :

```python
    embedding = Column(Vector(384))
```

par :

```python
    embedding = Column(Vector(1536))
```

- [ ] **Step 3 : Appliquer et vérifier la migration sur `qualicheck_test`**

Cette étape touche une vraie connexion Postgres — utiliser exclusivement
`qualicheck_test` (jamais `qualicheck`, qui contient les 245 vraies
règles). `make migration-test` a déjà été exécuté plus tôt dans le
projet ; cette commande re-applique jusqu'à la nouvelle tête (0011) sur
cette base dédiée.

Run: `make migration-test`
Expected : la commande se termine sans erreur (alembic upgrade jusqu'à 0011).

Run :
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck_test -c "
SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a
WHERE a.attrelid = 'regle'::regclass AND a.attname = 'embedding';
"
```
Expected : `vector(1536)`.

Run :
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck_test -c "\d regle" | grep embedding
```
Expected : la ligne `Indexes:` liste `regle_embedding_idx` (hnsw).

- [ ] **Step 4 : Vérifier la symétrie du downgrade sur `qualicheck_test`**

Run :
```bash
cd app/migration && POSTGRES_DB=qualicheck_test uv run alembic downgrade -1 && cd ../..
```
Expected : pas d'erreur.

Run (même requête qu'au Step 3) :
```bash
docker exec qualicheck-postgres psql -U qualicheck -d qualicheck_test -c "
SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a
WHERE a.attrelid = 'regle'::regclass AND a.attname = 'embedding';
"
```
Expected : `vector(384)` (retour à l'état d'avant la migration).

Puis ré-appliquer pour laisser `qualicheck_test` à la tête (nécessaire aux
tâches suivantes) :

Run: `make migration-test`
Expected : retour à `vector(1536)`, aucune erreur.

- [ ] **Step 5 : Ajouter un test permanent de schéma**

Dans `tests/migration/test_migration.py`, ajouter (ce test lit la vraie
base `qualicheck` en lecture seule — schéma uniquement, cohérent avec les
tests existants du fichier) :

```python
def test_colonne_embedding_dimension_1536(conn):
    """embedding doit être en vector(1536), avec son index HNSW."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            WHERE a.attrelid = 'regle'::regclass AND a.attname = 'embedding';
        """)
        type_actuel = cur.fetchone()[0]
    assert type_actuel == "vector(1536)", f"Type embedding inattendu : {type_actuel}"

    with conn.cursor() as cur:
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'regle' AND indexname = 'regle_embedding_idx';
        """)
        index = cur.fetchone()
    assert index is not None, "Index regle_embedding_idx manquant"
```

Ce test lit la vraie base `qualicheck` — **la migration 0011 doit d'abord
être appliquée sur `qualicheck` elle-même** (pas seulement `qualicheck_test`)
pour que ce test passe. Run : `make migration` (applique jusqu'à la tête
sur la vraie base — opération non destructive, `ALTER COLUMN TYPE` sur une
colonne à `NULL` partout, aucune donnée perdue).

Run: `uv run pytest tests/migration/test_migration.py -v`
Expected : tous les tests passent, y compris le nouveau.

- [ ] **Step 6 : Lancer `ruff`**

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 7 : Commit**

```bash
git add app/migration/versions/0011_widen_embedding_dimension.py app/models/referentiel.py tests/migration/test_migration.py
git commit -m "$(cat <<'EOF'
feat: widen regle.embedding to vector(1536)

384 (hérité du choix MiniLM, disqualifié) tronquait significativement
l'information d'un chunk riche (jusqu'à ~950 tokens). 1536 = dimension
native de text-embedding-3-small. Fait maintenant : aucune donnée
réelle n'existe encore sur cette colonne.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2 : `app/ingestion/chunking.py` — construction du texte de chunk

**Files:**

- Create: `app/ingestion/chunking.py`
- Test: `tests/unit/ingestion/test_chunking.py`

**Interfaces:**

- Consumes : rien.
- Produces : `build_chunk_text(rule) -> str` — consommé par la Task 5
  (`scripts/embed_rules.py`, `scripts/ingestion.py`). `rule` est tout
  objet portant `intitule`, `contexte`, `solution`, `controle`,
  `guide_analyse`, `tags`, `phases` (compatible `EnrichedRule`).

- [ ] **Step 1 : Écrire les tests qui échouent**

Créer `tests/unit/ingestion/test_chunking.py` :

```python
"""
Tests unitaires pour app/ingestion/chunking.py

Teste la construction du texte de chunk (une règle = un chunk, structuré
avec labels).
"""
from app.ingestion.chunking import build_chunk_text
from app.ingestion.schema import EnrichedRule


def _rule(contexte=None):
    return EnrichedRule(
        id=1, number=1, intitule="Les images ont un attribut alt",
        theme="Contenus", contexte=contexte,
        solution="Ajouter alt descriptif", controle="Vérifier alt présent",
        objectifs=["Accessibilité"], tags=["HTML", "Images"], phases=["Intégration"],
        slug="images-alt",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Parcourez le DOM et vérifiez l'attribut alt.",
    )


def test_build_chunk_text_includes_all_labeled_sections():
    """Le chunk contient un label par champ, dans l'ordre attendu."""
    rule = _rule(contexte="Les images décoratives n'ont pas besoin d'alt.")

    chunk = build_chunk_text(rule)

    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Contexte : Les images décoratives n'ont pas besoin d'alt." in chunk
    assert "Solution : Ajouter alt descriptif" in chunk
    assert "Controle : Vérifier alt présent" in chunk
    assert "Guide d'analyse : Parcourez le DOM et vérifiez l'attribut alt." in chunk
    assert "Tags : HTML, Images" in chunk
    assert "Phases : Intégration" in chunk


def test_build_chunk_text_omits_contexte_when_none():
    """Aucune ligne Contexte si le champ est None."""
    rule = _rule(contexte=None)

    chunk = build_chunk_text(rule)

    assert "Contexte" not in chunk
    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Solution : Ajouter alt descriptif" in chunk
```

- [ ] **Step 2 : Vérifier que les tests échouent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: `ModuleNotFoundError: No module named 'app.ingestion.chunking'`

- [ ] **Step 3 : Créer `app/ingestion/chunking.py`**

```python
"""
Construction du texte de chunk pour l'embedding.

Une règle = un chunk (décision actée, cf.
conception/2_ingestion/L_chunking_embedding_indexation.md §3 et
conception/2_ingestion/ingestion.md §Étape 5) : le texte assemble tous les
champs pertinents d'une règle, structuré avec des labels par champ.
"""


def build_chunk_text(rule) -> str:
    """
    Assemble le texte structuré d'un chunk à partir des champs d'une règle.

    Args:
        rule: objet portant intitule, contexte, solution, controle,
            guide_analyse, tags, phases (ex. EnrichedRule)

    Returns:
        Texte structuré avec labels, une section par champ. La section
        "Contexte" est omise si rule.contexte est None.
    """
    parts = [f"Intitulé : {rule.intitule}"]
    if rule.contexte:
        parts.append(f"Contexte : {rule.contexte}")
    parts.append(f"Solution : {rule.solution}")
    parts.append(f"Controle : {rule.controle}")
    parts.append(f"Guide d'analyse : {rule.guide_analyse}")
    parts.append(f"Tags : {', '.join(rule.tags)}")
    parts.append(f"Phases : {', '.join(rule.phases)}")
    return "\n".join(parts)
```

- [ ] **Step 4 : Vérifier que les tests passent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: `2 passed`

- [ ] **Step 5 : Commit**

```bash
git add app/ingestion/chunking.py tests/unit/ingestion/test_chunking.py
git commit -m "$(cat <<'EOF'
feat: add build_chunk_text (one rule = one chunk)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3 : `app/ingestion/embedding.py` — client d'embedding Azure

**Files:**

- Create: `app/ingestion/embedding.py`
- Modify: `app/ingestion/manifest.yml`
- Test: `tests/unit/ingestion/test_embedding.py`

**Interfaces:**

- Consumes : `app.ingestion.llm_client.load_manifest()` (déjà existant).
- Produces : `EmbeddingClient` avec méthode
  `embed_batch(texts: list[str]) -> list[list[float]]` et attribut
  `total_tokens: int` (accumulé across appels) — consommé par la Task 5.

**⚠️ Aucun test de cette tâche ne doit faire de requête réseau réelle** —
le client `openai.OpenAI` est entièrement mocké dans les tests.

- [ ] **Step 1 : Ajouter le rôle `embedding` à `manifest.yml`**

Dans `app/ingestion/manifest.yml`, ajouter à la suite du rôle
`enrichissement` existant :

```yaml
embedding:
  modele: text-embedding-3-small
  env_var: AZURE_MODEL_TEXT_EMBEDDING_SMALL
  # Prix (€ pour 1M tokens d'entrée) — tarif public Azure/OpenAI (~0,02 $/M
  # tokens) converti en euros par estimation, aucune facture Azure réelle
  # disponible pour l'instant (premier usage réel de ce modèle). À corriger
  # dès qu'une vraie facture existe — même logique que le rôle enrichissement.
  prix_entree_par_million: 0.0184
```

- [ ] **Step 2 : Écrire les tests qui échouent**

Créer `tests/unit/ingestion/test_embedding.py` :

```python
"""
Tests unitaires pour app/ingestion/embedding.py

Teste le client d'embedding Azure — aucune requête réseau réelle, le
client openai est entièrement mocké.
"""
from unittest.mock import MagicMock, patch

from app.ingestion.embedding import EmbeddingClient


def _mock_embeddings_response(vectors, total_tokens):
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    response.usage.total_tokens = total_tokens
    return response


class TestEmbeddingClient:
    """Tests du client d'embedding."""

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_returns_vectors_in_order(self, mock_openai_class):
        """embed_batch retourne les vecteurs dans le même ordre que les textes."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.return_value = _mock_embeddings_response(
            vectors=[[0.1, 0.2], [0.3, 0.4]], total_tokens=42
        )

        client = EmbeddingClient()
        vectors = client.embed_batch(["texte un", "texte deux"])

        assert vectors == [[0.1, 0.2], [0.3, 0.4]]
        assert client.total_tokens == 42

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_passes_dimensions_1536_explicitly(self, mock_openai_class):
        """L'appel API demande explicitement dimensions=1536, jamais 384."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.return_value = _mock_embeddings_response(
            vectors=[[0.1] * 1536], total_tokens=10
        )

        client = EmbeddingClient()
        client.embed_batch(["texte"])

        call_kwargs = mock_client_instance.embeddings.create.call_args.kwargs
        assert call_kwargs["dimensions"] == 1536

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_accumulates_tokens_across_calls(self, mock_openai_class):
        """total_tokens s'accumule sur plusieurs appels (plusieurs lots)."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.side_effect = [
            _mock_embeddings_response(vectors=[[0.1]], total_tokens=10),
            _mock_embeddings_response(vectors=[[0.2]], total_tokens=15),
        ]

        client = EmbeddingClient()
        client.embed_batch(["texte un"])
        client.embed_batch(["texte deux"])

        assert client.total_tokens == 25
```

- [ ] **Step 3 : Vérifier que les tests échouent**

Run: `uv run pytest tests/unit/ingestion/test_embedding.py -v`
Expected: `ModuleNotFoundError: No module named 'app.ingestion.embedding'`

- [ ] **Step 4 : Créer `app/ingestion/embedding.py`**

```python
"""
Client pour le calcul d'embeddings via Azure text-embedding-3-small.

Utilise le client openai brut (pas langchain) : la réponse de l'API
expose le nombre de tokens consommés (response.usage.total_tokens),
nécessaire au suivi de coût — l'interface Embeddings de langchain
(embed_documents()) ne les expose pas.
"""

import os

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .llm_client import load_manifest

EMBEDDING_DIMENSIONS = 1536


class EmbeddingClient:
    """Client pour le calcul d'embeddings de règles (une règle = un chunk)."""

    def __init__(self):
        """Initialise le client Azure OpenAI (embeddings)."""
        manifest = load_manifest()
        role = manifest["embedding"]
        self.model_name = role["modele"]
        self.deployment_name = os.getenv(role["env_var"])

        self.client = OpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            max_retries=0,
        )
        self.total_tokens = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Calcule les embeddings d'un lot de textes (jusqu'à 50).

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        autre), avec backoff exponentiel (2s, 4s, 8s).

        Args:
            texts: Chunks à vectoriser (un par règle), un lot à la fois

        Returns:
            Vecteurs à 1536 dimensions, dans le même ordre que texts
        """
        response = self.client.embeddings.create(
            model=self.deployment_name,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        self.total_tokens += response.usage.total_tokens
        return [item.embedding for item in response.data]
```

- [ ] **Step 5 : Vérifier que les tests passent**

Run: `uv run pytest tests/unit/ingestion/test_embedding.py -v`
Expected: `3 passed`

- [ ] **Step 6 : Lancer `ruff`**

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 7 : Commit**

```bash
git add app/ingestion/embedding.py app/ingestion/manifest.yml tests/unit/ingestion/test_embedding.py
git commit -m "$(cat <<'EOF'
feat: add EmbeddingClient (Azure text-embedding-3-small, dimensions=1536)

Client openai brut (pas langchain) pour accéder au total_tokens réel de
la réponse, nécessaire au suivi de coût. dimensions=1536 passé
explicitement à chaque appel — jamais 384.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4 : Brancher l'embedding dans `EnrichedRule` et `upsert_rule()`

**Files:**

- Modify: `app/ingestion/schema.py`
- Modify: `app/ingestion/stockage.py`
- Test: `tests/integration/ingestion/test_stockage_embedding.py` (nouveau)

**Interfaces:**

- Consumes : rien de nouveau (les Tasks 1-3 ne sont pas des dépendances
  directes de code ici, seulement de schéma — la colonne `embedding` doit
  être en `vector(1536)`, déjà fait par la Task 1).
- Produces : `EnrichedRule.embedding: list[float] | None` — consommé par
  la Task 5. `upsert_rule()` écrit cette valeur en base.

Ce test est un test d'intégration Postgres : utiliser exclusivement
`POSTGRES_TEST_DB` (`qualicheck_test`), jamais `POSTGRES_DB` — convention
actée le 2026-07-25 (`CLAUDE.md`, « Tests d'intégration Postgres
destructeurs »).

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `tests/integration/ingestion/test_stockage_embedding.py` :

```python
"""
Test d'intégration : embedding survit à un cycle store -> load.
Nécessite qualicheck-postgres démarré et POSTGRES_TEST_DB migrée
(make migration-test, migration 0011 incluse — vector(1536)).
"""
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.schema import EnrichedRule
from app.ingestion.stockage import clear_opquast_tables, load_enriched_rules_from_db, store_rules

load_dotenv()


def _database_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_embedding_round_trip(session):
    """Un embedding de 1536 flottants survit à un cycle store -> load."""
    clear_opquast_tables(session)

    vecteur = [0.001 * i for i in range(1536)]
    rule = EnrichedRule(
        id=1, number=1, intitule="Règle avec embedding", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", embedding=vecteur,
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].embedding is not None
    assert len(by_number[1].embedding) == 1536
    assert by_number[1].embedding[0] == pytest.approx(0.0)
    assert by_number[1].embedding[1] == pytest.approx(0.001)

    clear_opquast_tables(session)


def test_embedding_stays_null_when_not_provided(session):
    """Une règle sans embedding fourni reste NULL en base (pas de valeur par défaut)."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle sans embedding", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].embedding is None

    clear_opquast_tables(session)
```

- [ ] **Step 2 : Vérifier que le test échoue**

Run: `uv run pytest tests/integration/ingestion/test_stockage_embedding.py -v`
Expected: `AttributeError: 'EnrichedRule' object has no attribute 'embedding'`
sur la ligne `assert by_number[1].embedding is not None`. Pydantic v2
ignore silencieusement les kwargs non déclarés à la construction (pas
d'erreur avant cette assertion) — c'est la ligne de l'assertion qui doit
échouer, pas la construction de `EnrichedRule`.

- [ ] **Step 3 : Ajouter `embedding` à `EnrichedRule`**

Dans `app/ingestion/schema.py`, dans la classe `EnrichedRule`, ajouter
après `prompt_version: int | None = None` :

```python
    embedding: list[float] | None = None
```

- [ ] **Step 4 : Écrire `embedding` dans `upsert_rule()`**

Dans `app/ingestion/stockage.py`, dans `upsert_rule()`, ajouter juste
après la ligne `regle.prompt_version = enriched_rule.prompt_version` (et
avant `regle.updated_at = now`) :

```python
    if enriched_rule.embedding is not None:
        regle.embedding = enriched_rule.embedding
```

- [ ] **Step 5 : Ajouter `embedding` à la reconstruction dans `load_enriched_rules_from_db()`**

Dans `app/ingestion/stockage.py`, dans `load_enriched_rules_from_db()`,
dans la construction de l'objet `EnrichedRule`, ajouter après
`prompt_version=regle.prompt_version,` :

```python
            embedding=regle.embedding,
```

(`pgvector` convertit déjà la valeur lue en `list[float]` côté SQLAlchemy
— `Vector._from_db()` retourne directement une liste Python, pas besoin de
conversion supplémentaire.)

- [ ] **Step 6 : Vérifier que les tests passent**

Run: `uv run pytest tests/integration/ingestion/test_stockage_embedding.py -v`
Expected: `2 passed`

- [ ] **Step 7 : Lancer la suite complète et `ruff`**

Run: `uv run pytest tests/ -v`
Expected: tous les tests passent (aucune régression sur les tests
existants de `stockage.py`/`schema.py`).

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 8 : Commit**

```bash
git add app/ingestion/schema.py app/ingestion/stockage.py tests/integration/ingestion/test_stockage_embedding.py
git commit -m "$(cat <<'EOF'
feat: add embedding field to EnrichedRule and upsert_rule()

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5 : Points d'entrée — `scripts/embed_rules.py` + Étape 6 dans `scripts/ingestion.py`

**Files:**

- Create: `scripts/embed_rules.py`
- Modify: `scripts/ingestion.py`
- Modify: `Makefile` (nouvelle cible `embed-rules`)
- Modify: `CLAUDE.md` (tableau des cibles Makefile)
- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes : `app.ingestion.embedding.EmbeddingClient` (Task 3),
  `app.ingestion.chunking.build_chunk_text` (Task 2),
  `app.ingestion.stockage.load_enriched_rules_from_db`/`upsert_rule`
  (Task 4), `app.ingestion.llm_client.load_manifest`.
- Produces : rien de consommé par une tâche ultérieure — dernière tâche
  du plan.

**⚠️ Ne pas exécuter `scripts/embed_rules.py` ni `scripts/ingestion.py`
pour de vrai** — cela déclencherait un appel réel (et payant, même si
minime) à l'API Azure embeddings. Vérification uniquement via
`ruff check` et `python -m py_compile` (jamais d'exécution de `main()`).

- [ ] **Step 1 : Créer `scripts/embed_rules.py`**

```python
"""Point d'entrée pour le calcul d'embedding de toutes les règles.

Recalcule l'embedding des 245 règles à chaque exécution (pas seulement
celles à NULL) — plus simple, coût négligeable sur ce volume. Fail-fast :
toute erreur arrête immédiatement le script avec un code de sortie
non-nul.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunking import build_chunk_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.stockage import load_enriched_rules_from_db, upsert_rule  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

BATCH_SIZE = 50


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

    engine = get_engine()

    logger.info("=== embed_rules : démarrage ===")
    progress_logger.info("=== embed_rules : démarrage ===")

    try:
        with Session(engine) as session:
            enriched_rules = load_enriched_rules_from_db(session)

        rules = enriched_rules.regles
        progress_logger.info(f"embed_rules : {len(rules)} règle(s) à vectoriser")

        client = EmbeddingClient()

        for i in range(0, len(rules), BATCH_SIZE):
            batch = rules[i : i + BATCH_SIZE]
            texts = [build_chunk_text(rule) for rule in batch]
            vectors = client.embed_batch(texts)
            for rule, vector in zip(batch, vectors, strict=True):
                rule.embedding = vector
            progress_logger.info(
                f"embed_rules : lot {i // BATCH_SIZE + 1} ({len(batch)} règles) — OK"
            )

        with Session(engine) as session:
            for rule in rules:
                upsert_rule(session, rule)
            session.commit()

        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = f"embed_rules — Tokens : {client.total_tokens}, coût estimé : {cost:.4f} €"
        logger.info(summary)
        progress_logger.info(summary)

    except Exception as e:
        logger.error("embed_rules : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== embed_rules : succès ===")
    progress_logger.info("=== embed_rules : succès ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2 : Vérifier la syntaxe (sans exécuter)**

Run: `uv run ruff check scripts/embed_rules.py`
Expected: `All checks passed!`

Run: `uv run python -m py_compile scripts/embed_rules.py`
Expected: aucune sortie, code de sortie 0.

- [ ] **Step 3 : Ajouter l'Étape 6 à `scripts/ingestion.py`**

Dans `scripts/ingestion.py`, ajouter les imports nécessaires en tête :

```python
from app.ingestion.chunking import build_chunk_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
```

Puis, juste après le bloc de l'Étape 3 (Enrichissement, après le calcul du
coût `enriched.input_tokens`/`enriched.output_tokens`) et avant l'Étape 4
(Stockage), insérer :

```python
        try:
            logger.info("Étape 6 — Embedding : démarrage")
            progress_logger.info("Étape 6 — Embedding : démarrage")
            embed_client = EmbeddingClient()
            for i in range(0, len(enriched.regles), 50):
                batch = enriched.regles[i : i + 50]
                texts = [build_chunk_text(rule) for rule in batch]
                vectors = embed_client.embed_batch(texts)
                for rule, vector in zip(batch, vectors, strict=True):
                    rule.embedding = vector
            logger.info("Étape 6 — Embedding : terminée")
        except Exception as e:
            logger.error("Étape 6 — Embedding : ÉCHEC (%s)", e)
            sys.exit(1)
```

(Placé avant le bloc `try: ... Étape 4 — Stockage`, pour que chaque
`EnrichedRule` porte déjà son `embedding` au moment de l'appel à
`store_rules()`.)

- [ ] **Step 4 : Vérifier la syntaxe de `scripts/ingestion.py`**

Run: `uv run ruff check scripts/ingestion.py`
Expected: `All checks passed!`

Run: `uv run python -m py_compile scripts/ingestion.py`
Expected: aucune sortie, code de sortie 0.

- [ ] **Step 5 : Ajouter la cible Makefile**

Dans `Makefile`, section « Ingestion et données réelles », après
`enrich-again` :

```makefile
## Recalcule l'embedding de toutes les règles (Azure text-embedding-3-small,
## dimensions=1536), puis sauvegarde les données réelles
embed-rules:
	uv run python scripts/embed_rules.py
	$(MAKE) export_sql
```

Mettre à jour `.PHONY` pour y ajouter `embed-rules`.

- [ ] **Step 6 : Documenter dans `CLAUDE.md`**

Ajouter une ligne au tableau des cibles Makefile, après `make enrich-again` :

```markdown
| `make embed-rules` | Recalcule l'embedding de toutes les règles (`text-embedding-3-small`, `dimensions=1536`), puis `make export_sql` |
```

- [ ] **Step 7 : Ajouter une entrée `CHANGELOG.md`**

Ajouter une entrée datée (2026-07-26, Claude Code) décrivant : la
migration 0011 (`vector(384)`→`vector(1536)`), `app/ingestion/chunking.py`,
`app/ingestion/embedding.py`, le rôle `embedding` dans `manifest.yml`,
`scripts/embed_rules.py`, l'Étape 6 dans `scripts/ingestion.py`, la cible
`make embed-rules` — et préciser explicitement qu'aucun appel réel à
l'API Azure embeddings n'a eu lieu dans ce chantier.

- [ ] **Step 8 : Lancer la suite complète de tests et `ruff`**

Run: `uv run pytest tests/ -v`
Expected: tous les tests passent (aucun `FAILED`).

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 9 : Commit**

```bash
git add scripts/embed_rules.py scripts/ingestion.py Makefile CLAUDE.md CHANGELOG.md
git commit -m "$(cat <<'EOF'
feat: add scripts/embed_rules.py and Étape 6 in scripts/ingestion.py

Point d'entrée CLI (backfill, recalcule toutes les règles) sur le
modèle de scripts/enrich_again.py, plus intégration au pipeline complet
pour les futures ré-ingestions. Non exécuté pour de vrai dans le cadre
de ce chantier (appel Azure embeddings réel réservé à un lancement
manuel délibéré).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Fin de plan

Après la Task 5, utiliser superpowers:finishing-a-development-branch — pas
de nouvelle branche (travail resté sur `feature`, comme les chantiers D à
L). Le premier calcul réel d'embedding (`make embed-rules` contre les 245
vraies règles) reste une décision et une action de David, hors périmètre
de ce plan.
