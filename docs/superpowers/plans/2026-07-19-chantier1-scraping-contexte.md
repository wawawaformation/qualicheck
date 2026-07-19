# Chantier 1 — Correction scraping + champ `contexte` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corriger le scraping Opquast (footer parasite, listes `<ul>` ignorées) et ajouter un champ `contexte` (texte explicatif) qui traverse tout le pipeline d'ingestion jusqu'au prompt LLM.

**Architecture:** `scrape_rule()` est réécrit pour borner l'extraction à `div.c-rule-content` et cibler les headings par classe émoji stable (`c-emoji-tools`, `c-emoji-check`), avec une fonction utilitaire `extract_content_after()` qui collecte `<p>`/`<ul>` jusqu'au `<h2>` suivant. Le champ `contexte` (nullable, `.c-rule-hero__subtitle`) est ajouté aux 3 schémas Pydantic, à la colonne BDD (`TEXT`), au stockage, et au prompt d'enrichissement.

**Tech Stack:** Python, BeautifulSoup4, Pydantic, SQLAlchemy, Alembic, pytest.

## Global Constraints

- Spec source : `conception/2_ingestion/D_chantier1_scraping_contexte.md`
- Sentinelle mot-clé footer : **interdite** (bornage structurel suffit — pas de code défensif pour un scénario impossible)
- Fail-fast conservé : `solution`/`controle` vide après extraction → `ValueError`
- `contexte` : nullable partout (`str | None`), type BDD `TEXT`
- Retry LLM existant (3 tentatives, backoff) : ne pas y toucher dans ce chantier
- Avant tout appel LLM réel : dump JSON de l'objet `Rules` dans `./tmp/` pour validation visuelle
- Ne pas toucher aux étapes 5-7 (chunking/embedding/indexation) ni au prompt V4 (chantier 2) au-delà du branchement minimal `{contexte}`

---

## Task 1: Réécriture de `scrape_rule()` avec extraction bornée

**Files:**
- Modify: `app/ingestion/acquisition.py:74-121`
- Test: `tests/unit/ingestion/test_acquisition.py:96-120`

**Interfaces:**
- Consumes: rien de nouveau (BeautifulSoup déjà importé)
- Produces: `scrape_rule(slug: str) -> dict[str, str | None]` avec clés `"solution"`, `"controle"`, `"contexte"` — consommé par `acquire_rules()` (Task 2) et par les tests d'intégration

- [ ] **Step 1: Écrire les tests qui échouent (structure réelle Opquast)**

Remplacer entièrement la classe `TestScrapeRule` dans `tests/unit/ingestion/test_acquisition.py` (lignes 96-120) :

```python
class TestScrapeRule:
    """Tests de la fonction scrape_rule."""

    HTML_SIMPLE = """
    <html>
        <body>
            <div class="c-rule-hero__subtitle">Texte explicatif de la règle.</div>
            <div class="c-rule-content">
                <h2 class="c-emoji-target">Objectif</h2>
                <ul><li>Permettre X</li></ul>
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Mettre en place un flux RSS pour les nouveaux contenus</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Vérifier la présence d'un flux RSS valide</p>
            </div>
            <footer><p>SAS au capital de 1000 euros - Lucien Granet</p></footer>
        </body>
    </html>
    """

    HTML_MULTI_BLOCS = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Ne pas utiliser d'ouverture automatique de fenêtre</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Cette bonne pratique est à vérifier manuellement.</p>
                <p>Dans toutes les pages internes du site :</p>
                <ul>
                    <li>Vérifier que la navigation ne provoque pas de popup</li>
                    <li>Vérifier chaque lien externe</li>
                </ul>
            </div>
            <footer><p>SAS au capital de 1000 euros - Lucien Granet</p></footer>
        </body>
    </html>
    """

    HTML_NO_SUBTITLE = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Solution simple</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Contrôle simple</p>
            </div>
        </body>
    </html>
    """

    HTML_NO_CONTENT_DIV = """
    <html><body><p>Page inattendue</p></body></html>
    """

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_extracts_solution_and_controle(self, mock_get):
        """Vérifie l'extraction simple solution + controle + contexte."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_SIMPLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["solution"] == "Mettre en place un flux RSS pour les nouveaux contenus"
        assert result["controle"] == "Vérifier la présence d'un flux RSS valide"
        assert result["contexte"] == "Texte explicatif de la règle."

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_never_captures_footer(self, mock_get):
        """Vérifie que le footer n'est jamais capturé (bornage c-rule-content)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_SIMPLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert "SAS au capital" not in result["solution"]
        assert "SAS au capital" not in result["controle"]

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_collects_multiple_blocks_and_ul(self, mock_get):
        """Vérifie que plusieurs <p> + un <ul> sont tous capturés et concaténés (règle 154)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_MULTI_BLOCS
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        expected_controle = (
            "Cette bonne pratique est à vérifier manuellement.\n"
            "Dans toutes les pages internes du site :\n"
            "- Vérifier que la navigation ne provoque pas de popup\n"
            "- Vérifier chaque lien externe"
        )
        assert result["controle"] == expected_controle

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_contexte_none_when_subtitle_absent(self, mock_get):
        """Vérifie que contexte est None si .c-rule-hero__subtitle est absent."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_NO_SUBTITLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["contexte"] is None

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_raises_when_content_div_absent(self, mock_get):
        """Vérifie le fail-fast si c-rule-content est absent (structure inattendue)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_NO_CONTENT_DIV
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="c-rule-content"):
            scrape_rule("regle-exemple")
```

Ajouter en haut du fichier (après les imports existants) :

```python
import pytest
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_acquisition.py -v`
Expected: FAIL — `KeyError: 'contexte'` ou assertions sur le contenu (l'ancienne implémentation ne borne pas, ne gère pas `<ul>`, ne fournit pas `contexte`).

- [ ] **Step 3: Réécrire `scrape_rule()` et ajouter `extract_content_after()`**

Remplacer les lignes 74-121 de `app/ingestion/acquisition.py` :

```python
def extract_content_after(heading) -> str:
    """
    Collecte le contenu (texte) des frères d'un heading jusqu'au <h2> suivant.

    Chaque <p> devient un bloc de texte ; chaque <ul> devient un bloc où
    chaque <li> est rendu sur sa propre ligne préfixée par "- ".
    Les blocs sont joints par un saut de ligne.

    Args:
        heading: Élément BeautifulSoup <h2> de départ

    Returns:
        Texte extrait (chaîne vide si aucun contenu trouvé)
    """
    blocks = []
    for sibling in heading.find_next_siblings():
        if sibling.name == "h2":
            break
        if sibling.name == "p":
            text = sibling.get_text(strip=True)
            if text:
                blocks.append(text)
        elif sibling.name == "ul":
            items = [li.get_text(strip=True) for li in sibling.find_all("li")]
            if items:
                blocks.append("\n".join(f"- {item}" for item in items))

    return "\n".join(blocks)


def scrape_rule(slug: str) -> dict[str, str | None]:
    """
    Scrape les informations d'une règle Opquast depuis le site web pour extraire
    les champs `solution`, `controle` et `contexte`.

    L'extraction est bornée au conteneur `div.c-rule-content` : le pied de page
    du site est structurellement hors de ce conteneur et ne peut donc jamais
    être capturé par erreur.

    Args:
        slug: Slug de la règle

    Returns:
        Dictionnaire contenant "solution", "controle" (str) et "contexte" (str | None)

    Raises:
        ValueError: Si le conteneur de contenu est introuvable, ou si
            solution/controle sont vides après extraction
    """
    logger.info("Scraping rule: %s", slug)

    url = build_rule_url(slug)
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.find("div", class_="c-rule-content")
    if content is None:
        logger.error("c-rule-content container not found for slug: %s", slug)
        raise ValueError(f"c-rule-content container not found for slug: {slug}")

    subtitle = soup.find(class_="c-rule-hero__subtitle")
    contexte = subtitle.get_text(strip=True) if subtitle else None

    solution = ""
    controle = ""

    for heading in content.find_all("h2"):
        heading_classes = heading.get("class") or []

        if "c-emoji-tools" in heading_classes:
            solution = extract_content_after(heading)
            logger.debug("Found solution for slug: %s", slug)

        if "c-emoji-check" in heading_classes:
            controle = extract_content_after(heading)
            logger.debug("Found controle for slug: %s", slug)

    if not solution or not controle:
        logger.error("Solution or Controle not found for slug: %s", slug)
        raise ValueError(f"Solution or Controle not found for slug: {slug}")

    logger.info("Successfully scraped rule: %s", slug)
    return {
        "solution": solution,
        "controle": controle,
        "contexte": contexte,
    }
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_acquisition.py -v`
Expected: PASS (tous les tests de `TestScrapeRule`, plus `TestBuildRuleUrl` et `TestFetchApi` inchangés)

- [ ] **Step 5: Ruff**

Run: `cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/acquisition.py tests/unit/ingestion/test_acquisition.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/acquisition.py tests/unit/ingestion/test_acquisition.py
git commit -m "fix: bound scrape_rule to c-rule-content, capture ul lists, add contexte field"
```

---

## Task 2: Propager `contexte` dans les schémas Pydantic

**Files:**
- Modify: `app/ingestion/schema.py:10-68`
- Test: `tests/unit/ingestion/test_aggregation.py`

**Interfaces:**
- Consumes: `scrape_rule()` retourne désormais `"contexte": str | None` (Task 1)
- Produces: `RuleAcquisition.contexte`, `RuleAggregation.contexte`, `EnrichedRule.contexte` (tous `str | None = None`) — consommés par `aggregation.py` (aucun changement requis, passthrough Pydantic), `llm_client.py` (Task 3), `stockage.py` (Task 4)

- [ ] **Step 1: Lire le test d'agrégation existant pour connaître le pattern de fixture**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_aggregation.py -v --collect-only`
Expected: liste des tests existants (aucune modification requise si aucun test ne vérifie une liste stricte de champs — à confirmer par la lecture)

- [ ] **Step 2: Écrire le test qui échoue (contexte traverse RuleAggregation)**

Ajouter à `tests/unit/ingestion/test_aggregation.py` (à la fin du fichier, adapter l'import si besoin) :

```python
from app.ingestion.schema import RuleAggregation


class TestContexteField:
    """Vérifie que le champ contexte est optionnel et traverse RuleAggregation."""

    def _base_kwargs(self):
        return dict(
            id=1,
            number=1,
            intitule="Règle test",
            theme="Thème",
            objectifs=["Objectif"],
            tags=["Tag"],
            phases=["Phase"],
            slug="regle-test",
            solution="Solution",
            controle="Contrôle",
        )

    def test_contexte_defaults_to_none(self):
        rule = RuleAggregation(**self._base_kwargs())
        assert rule.contexte is None

    def test_contexte_accepts_string(self):
        rule = RuleAggregation(**self._base_kwargs(), contexte="Texte explicatif")
        assert rule.contexte == "Texte explicatif"
```

- [ ] **Step 3: Lancer le test, vérifier qu'il échoue**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_aggregation.py::TestContexteField -v`
Expected: FAIL — `contexte` n'est pas un champ reconnu (Pydantic lève une erreur ou l'attribut n'existe pas selon la config du modèle)

- [ ] **Step 4: Ajouter `contexte` aux 3 schémas**

Dans `app/ingestion/schema.py`, ajouter `contexte: str | None = None` :

Dans `RuleAcquisition` (après `slug: str`, ligne 20) :
```python
    slug: str
    contexte: str | None = None
    solution: str | None = Field(default=None)
    controle: str | None = Field(default=None)
```

Dans `RuleAggregation` (après `slug: str`, ligne 35) :
```python
    slug: str
    contexte: str | None = None
    solution: str
    controle: str
```

`EnrichedRule` hérite de `RuleAggregation` par `class EnrichedRule(RuleAggregation)` — aucun ajout nécessaire, le champ est déjà hérité.

- [ ] **Step 5: Lancer les tests, vérifier qu'ils passent**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_aggregation.py -v`
Expected: PASS (tous les tests, y compris `TestContexteField`)

- [ ] **Step 6: Ruff**

Run: `cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/schema.py tests/unit/ingestion/test_aggregation.py`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add app/ingestion/schema.py tests/unit/ingestion/test_aggregation.py
git commit -m "feat: add optional contexte field to ingestion Pydantic schemas"
```

---

## Task 3: Injection de `contexte` dans le prompt d'enrichissement

**Files:**
- Modify: `app/ingestion/prompts/enrich_rule.md:38-45`
- Modify: `app/ingestion/llm_client.py:21,58-67`
- Test: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**
- Consumes: `Rule.contexte` (= `RuleAggregation.contexte`, Task 2), `str | None`
- Produces: `LLMClient.load_prompt(rule)` inclut désormais la valeur de `contexte` (ou `"(non disponible)"` si `None`) dans le texte retourné — aucun changement de signature

- [ ] **Step 1: Lire le test d'enrichissement existant**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichment.py -v --collect-only`
Expected: liste des tests, pour repérer où ajouter un test sur `load_prompt`

- [ ] **Step 2: Écrire le test qui échoue**

Trouver le fichier de test du `LLMClient` (probablement `tests/unit/ingestion/test_enrichment.py` ou un fichier dédié `test_llm_client.py` — vérifier lequel importe `LLMClient`) :

```bash
grep -rl "LLMClient" tests/unit/ingestion/
```

Dans le fichier trouvé, ajouter :

```python
class TestLoadPromptContexte:
    """Vérifie que load_prompt injecte le champ contexte."""

    def test_load_prompt_includes_contexte_when_present(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_DEPLOYMENT_INGESTION", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
            contexte="Texte explicatif de la règle",
        )

        prompt = client.load_prompt(rule)

        assert "Texte explicatif de la règle" in prompt
        assert "{contexte}" not in prompt

    def test_load_prompt_handles_missing_contexte(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_DEPLOYMENT_INGESTION", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
        )

        prompt = client.load_prompt(rule)

        assert "(non disponible)" in prompt
        assert "{contexte}" not in prompt
```

- [ ] **Step 3: Lancer le test, vérifier qu'il échoue**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/ -v -k "load_prompt_includes_contexte or load_prompt_handles_missing"`
Expected: FAIL — `{contexte}` reste littéralement dans le texte retourné (placeholder non remplacé) ou `KeyError`

- [ ] **Step 4: Ajouter le placeholder au template**

Dans `app/ingestion/prompts/enrich_rule.md`, modifier le bloc "Contexte de la règle" (lignes 38-45) :

```markdown
## Contexte de la règle

- **Intitulé** : {intitule}
- **Texte explicatif** : {contexte}
- **Solution** : {solution}
- **Contrôle** : {controle}
- **Objectifs** : {objectifs}
- **Tags** : {tags}
- **Phases** : {phases}
```

- [ ] **Step 5: Mettre à jour `llm_client.py`**

Dans `app/ingestion/llm_client.py`, modifier `PROMPT_PLACEHOLDERS` (ligne 21) :

```python
PROMPT_PLACEHOLDERS = ["intitule", "contexte", "solution", "controle", "objectifs", "tags", "phases"]
```

Modifier `load_prompt()` (lignes 58-67) :

```python
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
```

- [ ] **Step 6: Lancer les tests, vérifier qu'ils passent**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/ -v`
Expected: PASS (tous les tests d'ingestion, y compris les 2 nouveaux)

- [ ] **Step 7: Ruff**

Run: `cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/llm_client.py tests/unit/ingestion/`
Expected: no errors

- [ ] **Step 8: Commit**

```bash
git add app/ingestion/prompts/enrich_rule.md app/ingestion/llm_client.py tests/unit/ingestion/
git commit -m "feat: inject contexte field into enrichment prompt"
```

---

## Task 4: Colonne BDD `contexte` + migration + stockage

**Files:**
- Modify: `app/models/referentiel.py:14-29`
- Create: `app/migration/versions/0006_add_regle_contexte.py`
- Modify: `app/ingestion/stockage.py:96-117,183-190`
- Test: `tests/integration/ingestion/` (nouveau fichier ou existant — vérifier à l'étape 1)

**Interfaces:**
- Consumes: `EnrichedRule.contexte` (Task 2/3), `Regle` modèle SQLAlchemy
- Produces: `Regle.contexte` colonne `TEXT NULL` ; `upsert_rule()` persiste `contexte` ; `load_enriched_rules_from_db()` relit `contexte`

- [ ] **Step 1: Vérifier l'état des migrations et conteneurs**

Run: `cd /media/david/projets/QualiCheck && docker compose ps`
Expected: conteneur `postgres` (ou nom équivalent) `Up`. Si non démarré, demander confirmation avant `make up` (démarrage de conteneurs n'est pas destructif, mais on respecte la consigne de vérifier l'état avant).

- [ ] **Step 2: Ajouter la colonne au modèle SQLAlchemy**

Dans `app/models/referentiel.py`, modifier la classe `Regle` (ligne 20, après `intitule`) :

```python
    intitule = Column(String(255), nullable=False, unique=True)
    contexte = Column(Text, nullable=True)
    solution = Column(String(1024), nullable=False)
```

- [ ] **Step 3: Créer la migration Alembic**

Créer `app/migration/versions/0006_add_regle_contexte.py` :

```python
"""Add contexte column to regle

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("regle", sa.Column("contexte", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("regle", "contexte")
```

- [ ] **Step 4: Appliquer la migration**

Run: `cd /media/david/projets/QualiCheck && make migration`
Expected: sortie confirmant l'application de `0006` sans erreur

- [ ] **Step 5: Vérifier la colonne en BDD**

Run: `cd /media/david/projets/QualiCheck && docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\d regle" | grep contexte`

(adapter le nom du service `postgres` si différent — vérifier via `docker compose ps` à l'étape 1)

Expected: une ligne `contexte | text |`

- [ ] **Step 6: Mettre à jour `upsert_rule()` pour persister `contexte`**

Dans `app/ingestion/stockage.py`, modifier les lignes 183-184 :

```python
    regle.intitule = enriched_rule.intitule
    regle.contexte = enriched_rule.contexte
    regle.solution = enriched_rule.solution
```

- [ ] **Step 7: Mettre à jour `load_enriched_rules_from_db()` pour relire `contexte`**

Dans `app/ingestion/stockage.py`, modifier les lignes 96-106 (ajout de `contexte=regle.contexte,` après `intitule=`) :

```python
        enriched = EnrichedRule(
            id=regle.id,
            number=regle.numero,
            intitule=regle.intitule,
            contexte=regle.contexte,
            theme=theme,
            solution=regle.solution,
            controle=regle.controle,
            objectifs=objectifs_list,
            tags=tags_list,
            phases=phases_list,
            slug="",  # Pas stocké en BDD, laissé vide
            strategie_analyse=regle.strategie_analyse,
            strategie_justification=regle.strategie_justification,
            guide_analyse=regle.guide_analyse,
            strategie_source=regle.strategie_source,
            llm_provider=regle.llm_provider,
        )
```

- [ ] **Step 8: Écrire un test d'intégration stockage (round-trip contexte)**

Vérifier d'abord le fichier existant pour connaître le pattern de session/fixtures :

Run: `ls tests/integration/ingestion/ && cat tests/integration/ingestion/*.py 2>/dev/null | head -50`

S'il n'existe pas de fixture réutilisable, créer `tests/integration/ingestion/test_stockage_contexte.py` — adapter la connexion BDD au pattern déjà utilisé ailleurs dans le projet (`build_database_url()` de `scripts/test_storage.py` comme référence) :

```python
"""
Test d'intégration : round-trip du champ contexte via upsert_rule +
load_enriched_rules_from_db. Nécessite les conteneurs Docker démarrés
et la migration 0006 appliquée.
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


def test_contexte_round_trip(session):
    """Vérifie que contexte survit à un cycle store -> load, y compris None."""
    clear_opquast_tables(session)

    rule_with_contexte = EnrichedRule(
        id=1, number=1, intitule="Règle avec contexte", theme="Thème",
        contexte="Texte explicatif de test",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    rule_without_contexte = EnrichedRule(
        id=2, number=2, intitule="Règle sans contexte", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-2", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    store_rules(session, EnrichedRules([rule_with_contexte, rule_without_contexte]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].contexte == "Texte explicatif de test"
    assert by_number[2].contexte is None

    clear_opquast_tables(session)
```

- [ ] **Step 9: Lancer le test d'intégration**

Run: `cd /media/david/projets/QualiCheck && uv run pytest tests/integration/ingestion/test_stockage_contexte.py -v`
Expected: PASS (nécessite conteneurs up + migration 0006 appliquée, cf Steps 1/4)

- [ ] **Step 10: Lancer toute la suite pour non-régression**

Run: `cd /media/david/projets/QualiCheck && make test`
Expected: tous les tests passent (unitaires + intégration)

- [ ] **Step 11: Ruff**

Run: `cd /media/david/projets/QualiCheck && uv run ruff check app/models/referentiel.py app/migration/versions/0006_add_regle_contexte.py app/ingestion/stockage.py tests/integration/ingestion/`
Expected: no errors

- [ ] **Step 12: Commit**

```bash
git add app/models/referentiel.py app/migration/versions/0006_add_regle_contexte.py app/ingestion/stockage.py tests/integration/ingestion/
git commit -m "feat: add contexte column to regle table, wire through storage layer"
```

---

## Task 5: Validation pré-LLM — dump JSON de `Rules` dans `./tmp/`

**Files:**
- Modify: `scripts/ingestion_test.py` (ajout du dump, pas de nouveau fichier — réutilise le découpage étapes 1-2 déjà présent)

**Interfaces:**
- Consumes: `acquire_rules()` (Task 1, retourne des dicts incluant `contexte`), `aggregate_rules()` (Task 2, inchangé — passthrough Pydantic)
- Produces: fichier `tmp/rules_acquises.json` — consommé uniquement par inspection humaine, aucune dépendance de code aval

- [ ] **Step 1: Ajouter le dump JSON après l'étape d'agrégation**

Dans `scripts/ingestion_test.py`, après la ligne 84 (`progress_logger.info(f"Étape 2 — Agrégation : ...")`), insérer :

```python
        # Dump de validation manuelle avant tout appel LLM (chantier 1)
        import json
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "tmp"), exist_ok=True)
        dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tmp", "rules_acquises.json")
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in aggregated.regles], f, ensure_ascii=False, indent=2)
        progress_logger.info(f"Dump de validation écrit : {dump_path}")
```

- [ ] **Step 2: Exécuter le script (scraping réel des 245 règles, sans LLM)**

Run: `cd /media/david/projets/QualiCheck && uv run python scripts/ingestion_test.py`
Expected: exécution complète jusqu'au stockage avec bouchons ; le fichier `tmp/rules_acquises.json` est créé

- [ ] **Step 3: Confirmer le contenu à l'utilisateur pour inspection manuelle**

Ne pas continuer vers Task 6 avant que l'utilisateur ait inspecté `tmp/rules_acquises.json` (en particulier règles 154, 166, 111) et validé — conformément à la demande explicite de l'utilisateur de s'arrêter ici avant tout appel LLM.

- [ ] **Step 4: Ruff**

Run: `cd /media/david/projets/QualiCheck && uv run ruff check scripts/ingestion_test.py`
Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add scripts/ingestion_test.py
git commit -m "feat: dump acquired Rules to tmp/ for manual validation before LLM calls"
```

---

## Task 6: Mise à jour de `TODO_PIPELINE_INGESTION.md`

**Files:**
- Modify: `TODO_PIPELINE_INGESTION.md` (déjà en cours de modification manuelle par l'utilisateur — vérifier l'état avant d'éditer)

**Interfaces:**
- Consumes: aucune (documentation)
- Produces: aucune

- [ ] **Step 1: Lire l'état actuel du fichier**

Le fichier a des modifications non commitées de la session précédente (Étape 1 marquée `[~]`, section "Ingestion réelle & analyse" ajoutée). Relire avant d'éditer pour ne pas écraser.

Run: `cat TODO_PIPELINE_INGESTION.md`

- [ ] **Step 2: Cocher les items R1.1/R1.2/R1.3 réalisés**

Éditer la ligne concernant "À corriger" et "À ajouter (R1.3)" pour les passer à `[x]`, et ajouter une note sous "Ingestion réelle & analyse" indiquant que le chantier 1 est fait et que `tmp/rules_acquises.json` a été validé.

Pas de code à fournir ici — c'est une édition de documentation en langage naturel, à faire une fois le contenu du fichier relu (Step 1).

- [ ] **Step 3: Commit (uniquement si l'utilisateur valide ce commit — sinon laisser non commité comme lors de la session précédente)**

```bash
git add TODO_PIPELINE_INGESTION.md
git commit -m "docs: mark chantier 1 (scraping fix + contexte) as done in TODO"
```

---

## Self-Review Notes

- **Spec coverage** : section 4.1 → Task 1 ; 4.2 → Task 2 ; 4.3/4.4 → Task 4 ; 4.5 → Task 4 ; 4.6 → Task 3 ; section 5 (validation) → Task 5 ; section 3 tableau de décisions → reflété dans Global Constraints et dans chaque tâche concernée.
- **Type consistency** : `contexte: str | None = None` identique dans les 3 schémas (Task 2), `Regle.contexte = Column(Text, nullable=True)` (Task 4), `scrape_rule()` retourne `dict[str, str | None]` (Task 1) — cohérent de bout en bout.
- **Ordre des tâches** : Task 1 (scraping) et Task 2 (schémas) sont indépendantes mais Task 1 produit les clés que Task 2 rend acceptables en Pydantic — les faire dans l'ordre écrit évite un état intermédiaire où `acquire_rules()` retourne une clé `contexte` que `RuleAggregation` rejetterait (Pydantic ignore les clés en trop par défaut, donc l'ordre n'est pas strictement bloquant, mais suivre l'ordre du plan reste plus sûr).
- **Task 5 dépend de Tasks 1-4** : le dump JSON n'a de sens que si le scraping est corrigé et le champ `contexte` circule.
- **Task 6** dépend de la validation utilisateur post-Task 5 (le dump JSON doit être inspecté avant de clore le chantier).
