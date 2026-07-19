# Étape 3 — Enrichissement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement LLM-based enrichment of rules via Azure Kimi K2.6, transforming each `Rule` into an `EnrichedRule` with three strategy fields, retry logic, and comprehensive logging.

**Architecture:** 
- `LLMClient` encapsulates LangChain + Azure setup, handles retry logic and JSON parsing
- `enrich_rules()` orchestrates the transformation of a `Rules` collection into `EnrichedRules`
- Prompt is externalized to `prompts/enrich_rule.md` for easy iteration
- TDD approach: tests first, then implementation, frequent commits

**Tech Stack:** 
- LangChain 0.1.x+ (chains, JsonOutputParser, tenacity for retry)
- Azure OpenAI (Kimi K2.6 deployment)
- Pydantic for data validation
- Python logging for granular error/success tracking

## Global Constraints

- **Code:** English (class names, functions, variables)
- **Docs/comments:** French
- **Naming:** Follow existing patterns (Rule, Rules, enrich_rules)
- **Convention:** Alias imports where needed for clarity (e.g., `Rule = RuleAggregation`)
- **Logging:** Error + critical failures + final summary (no individual success logs per rule)
- **Fail-fast:** Raise exception on validation error, no partial enrichment
- **Testing:** Unit tests with mocks, no Azure integration tests in MVP
- **Python version:** 3.14+ (per pyproject.toml)

---

## Task 1: Add LangChain Dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: existing dependencies
- Produces: LangChain installed and available for imports

- [ ] **Step 1: Check current dependencies in pyproject.toml**

```bash
grep -A 10 "dependencies = " /media/david/projets/QualiCheck/pyproject.toml
```

Expected output shows current list ending with sqlalchemy, requests, python-dotenv, etc.

- [ ] **Step 2: Add LangChain dependencies to pyproject.toml**

Open `pyproject.toml` and update the `dependencies` list to add:
```python
dependencies = [
    "alembic>=1.18.5",
    "beautifulsoup4>=4.12.2",
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "pgvector>=0.5.0",
    "psycopg2-binary>=2.9.12",
    "pydantic>=2.13.4",
    "python-dotenv>=1.2.2",
    "requests>=2.34.2",
    "sqlalchemy>=2.0.51",
]
```

- [ ] **Step 3: Run uv sync to install new dependencies**

```bash
cd /media/david/projets/QualiCheck && uv sync
```

Expected: Dependencies installed without errors.

- [ ] **Step 4: Verify imports work**

```bash
python3 -c "from langchain_openai import AzureChatOpenAI; from langchain.output_parsers import JsonOutputParser; print('OK')"
```

Expected output: `OK`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock && git commit -m "chore: add langchain dependencies

- langchain>=0.1.0 : LLM chains and orchestration
- langchain-openai>=0.1.0 : Azure OpenAI integration

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Create EnrichedRule Pydantic Model

**Files:**
- Modify: `app/ingestion/schema.py`
- Test: `tests/unit/ingestion/test_enrichissement.py` (created in Task 3)

**Interfaces:**
- Consumes: `Rule` (from schema.py)
- Produces: `EnrichedRule(BaseModel)` with fields:
  - id, number, intitule, objectifs, tags, phases, slug, solution, controle (inherited from Rule context)
  - strategie_analyse: str (free text, no validation on allowed values)
  - strategie_justification: str (non-empty)
  - guide_analyse: str (non-empty)
  - strategie_source: str = "ia_import"
  - llm_provider: str = "kimi-k2.6"

- [ ] **Step 1: Read current schema.py to understand RuleAggregation structure**

```bash
head -50 /media/david/projets/QualiCheck/app/ingestion/schema.py
```

Note the fields of `RuleAggregation` and ensure you understand composition.

- [ ] **Step 2: Add EnrichedRule model to schema.py**

Append to the end of `app/ingestion/schema.py`:

```python


class EnrichedRule(RuleAggregation):
    """Règle complètement enrichie par l'agent LLM."""

    strategie_analyse: str
    strategie_justification: str
    guide_analyse: str
    strategie_source: str = "ia_import"
    llm_provider: str = "kimi-k2.6"

    @field_validator("strategie_analyse", "strategie_justification", "guide_analyse")
    @classmethod
    def non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("La chaîne ne peut pas être vide")
        return v
```

- [ ] **Step 3: Run ruff check to verify linting**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/schema.py
```

Expected: No errors (or auto-fix with `--fix` if needed).

- [ ] **Step 4: Quick manual test of EnrichedRule creation**

```bash
python3 << 'EOF'
from app.ingestion.schema import EnrichedRule

rule = EnrichedRule(
    id=1, number=1, intitule="Test", solution="Sol", controle="Ctrl",
    objectifs=["Obj"], tags=["Tag"], phases=["Phase"], slug="test",
    strategie_analyse="statique",
    strategie_justification="Explication",
    guide_analyse="Guide complet"
)
print(f"Created: {rule.number} — {rule.intitule}")
EOF
```

Expected output: `Created: 1 — Test`

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/schema.py && git commit -m "feat: add EnrichedRule pydantic model

- Extends RuleAggregation with enrichment fields
- strategie_analyse, strategie_justification, guide_analyse (all non-empty)
- Metadata: strategie_source='ia_import', llm_provider='kimi-k2.6'

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Create EnrichedRules Collection Class

**Files:**
- Modify: `app/ingestion/agregation.py`

**Interfaces:**
- Consumes: `EnrichedRule` (from schema.py)
- Produces: `EnrichedRules` class with:
  - `__init__(enriched_rules: list[EnrichedRule])` — validates non-empty
  - `enriched_rules` attribute (list)
  - `regles` property (alias for compatibility)

- [ ] **Step 1: Add EnrichedRules class to agregation.py**

Append to the end of `app/ingestion/agregation.py`:

```python


class EnrichedRules:
    """Collection de règles complètement enrichies (non-vide)."""

    def __init__(self, enriched_rules: list):
        if not enriched_rules:
            raise ValueError("Collection de règles enrichies ne peut pas être vide")
        self.enriched_rules = enriched_rules

    @property
    def regles(self):
        """Rétrocompatibilité : alias français pour accès à la liste."""
        return self.enriched_rules
```

- [ ] **Step 2: Run ruff check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/agregation.py
```

Expected: No errors.

- [ ] **Step 3: Manual test of EnrichedRules creation**

```bash
python3 << 'EOF'
from app.ingestion.schema import EnrichedRule
from app.ingestion.agregation import EnrichedRules

rule = EnrichedRule(
    id=1, number=1, intitule="Test", solution="Sol", controle="Ctrl",
    objectifs=["Obj"], tags=["Tag"], phases=["Phase"], slug="test",
    strategie_analyse="statique",
    strategie_justification="Explication",
    guide_analyse="Guide"
)

collection = EnrichedRules([rule])
print(f"Collection size: {len(collection.regles)}")

# Test empty collection raises error
try:
    EnrichedRules([])
    print("ERROR: should have raised ValueError")
except ValueError as e:
    print(f"OK: {e}")
EOF
```

Expected:
```
Collection size: 1
OK: Collection de règles enrichies ne peut pas être vide
```

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/agregation.py && git commit -m "feat: add EnrichedRules collection class

- Wraps list of EnrichedRule objects
- Validates non-empty on initialization (fail-fast)
- Provides regles property for compatibility

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Create Prompt File (Few-Shot)

**Files:**
- Create: `app/ingestion/prompts/enrich_rule.md`

**Interfaces:**
- Consumes: path from environment or hardcoded
- Produces: readable prompt text with placeholders for rule context

- [ ] **Step 1: Create prompts directory**

```bash
mkdir -p /media/david/projets/QualiCheck/app/ingestion/prompts
```

- [ ] **Step 2: Write enrich_rule.md with few-shot examples**

Create `app/ingestion/prompts/enrich_rule.md`:

```markdown
# Enrichissement de Règles Opquast

Tu es un expert en audit web et en qualité numérique. Tu vas analyser une règle Opquast et générer une stratégie d'analyse optimale.

## Tâche

Pour chaque règle, tu dois générer **exactement 3 champs JSON** :

1. **strategie_analyse** : méthode d'extraction pertinente
   - Exemples : "statique" (analyse HTML), "playwright" (navigation), "manuel" (non-automatisable)
   - Libre : tu peux proposer d'autres méthodes si pertinent
2. **strategie_justification** : explication courte du choix (1-2 phrases)
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable)

## Format de réponse

Réponds **uniquement** avec un objet JSON valide, sans texte supplémentaire :

```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "L'attribut alt est vérifiable via analyse du DOM sans interaction.",
  "guide_analyse": "Parcourez toutes les images (<img>) de la page. Vérifiez que chacune possède un attribut alt non-vide. Signalez les images sans alt ou avec alt vide."
}
```

## Contexte de la règle

- **Intitulé** : {intitule}
- **Solution** : {solution}
- **Contrôle** : {controle}
- **Objectifs** : {objectifs}
- **Tags** : {tags}
- **Phases** : {phases}

## Exemples

### Exemple 1 : Règle simple, vérification statique

**Règle :** Les images ont un attribut alt

**Solution :** Ajouter un attribut alt descriptif à chaque image.

**Contrôle :** Vérifier que toutes les images ont un attribut alt.

**Réponse attendue :**
```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "L'attribut alt est présent dans le DOM et vérifiable sans interaction navigateur.",
  "guide_analyse": "Parcourez toutes les balises <img>. Vérifiez que chacune possède l'attribut alt avec une valeur non-vide. Les images décoratives peuvent avoir alt=''. Signalez les images sans alt."
}
```

### Exemple 2 : Règle complexe, nécessite interaction

**Règle :** Les contenus chargés dynamiquement sont accessibles

**Solution :** Implémenter un chargement accessible avec ARIA et gestion du focus.

**Contrôle :** Vérifier que les contenus chargés dynamiquement sont annoncés aux lecteurs d'écran.

**Réponse attendue :**
```json
{
  "strategie_analyse": "playwright",
  "strategie_justification": "Nécessite d'interagir avec la page (clic, scroll) pour déclencher le chargement dynamique et vérifier l'accessibilité.",
  "guide_analyse": "Utilisez Playwright pour déclencher les événements qui chargent le contenu dynamiquement. Analysez le DOM modifié et vérifiez les annonces ARIA (aria-live, aria-label). Testez l'ordre de tabulation après le chargement."
}
```

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
```

- [ ] **Step 3: Verify file exists and is readable**

```bash
cat /media/david/projets/QualiCheck/app/ingestion/prompts/enrich_rule.md | head -20
```

Expected: First 20 lines of the prompt appear.

- [ ] **Step 4: Commit**

```bash
git add app/ingestion/prompts/enrich_rule.md && git commit -m "docs: add few-shot prompt for LLM enrichment

- Few-shot examples (statique, playwright strategies)
- JSON format specification
- Placeholders for rule context (intitule, solution, etc.)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Create LLMClient with LangChain Integration

**Files:**
- Create: `app/ingestion/llm_client.py`

**Interfaces:**
- Consumes: 
  - `.env` variables: `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_DEPLOYMENT_INGESTION`
  - `Rule` from schema.py
  - Prompt file at `app/ingestion/prompts/enrich_rule.md`
- Produces: `LLMClient` class with method `enrich_single_rule(rule: Rule) -> EnrichedRule`

- [ ] **Step 1: Write failing test for LLMClient**

Create `tests/unit/ingestion/test_enrichissement.py`:

```python
"""
Tests unitaires pour app/ingestion/enrichissement.py et app/ingestion/llm_client.py

Teste l'enrichissement LLM de règles avec retry logic et parsing JSON.
"""

from unittest.mock import patch, MagicMock
from app.ingestion.schema import Rule, EnrichedRule
from app.ingestion.llm_client import LLMClient


class TestLLMClient:
    """Tests du client LangChain + Azure."""

    @patch("app.ingestion.llm_client.AzureChatOpenAI")
    def test_enrich_single_rule_success(self, mock_azure_llm):
        """Enrichit une règle avec succès."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        # Mock la réponse LLM
        mock_response = {
            "strategie_analyse": "statique",
            "strategie_justification": "Vérification simple du DOM",
            "guide_analyse": "Parcourez toutes les images et vérifiez l'attribut alt."
        }

        # Mock le parser pour retourner le dict
        with patch("app.ingestion.llm_client.JsonOutputParser") as mock_parser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = mock_response
            mock_parser.return_value = mock_parser_instance

            client = LLMClient()
            rule = Rule(
                id=1, number=1,
                intitule="Les images ont un attribut alt",
                solution="Ajouter alt descriptif",
                controle="Vérifier alt présent",
                objectifs=["Accessibilité"],
                tags=["HTML"],
                phases=["Intégration"],
                slug="images-alt"
            )

            enriched = client.enrich_single_rule(rule)

            assert isinstance(enriched, EnrichedRule)
            assert enriched.strategie_analyse == "statique"
            assert enriched.strategie_justification == "Vérification simple du DOM"
            assert enriched.guide_analyse == "Parcourez toutes les images et vérifiez l'attribut alt."
            assert enriched.strategie_source == "ia_import"
            assert enriched.llm_provider == "kimi-k2.6"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestLLMClient::test_enrich_single_rule_success -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.ingestion.llm_client'"

- [ ] **Step 3: Create llm_client.py with minimal implementation**

Create `app/ingestion/llm_client.py`:

```python
"""
Client LangChain pour enrichissement LLM via Azure Kimi K2.6.

Gère l'intégration Azure OpenAI, le parsing JSON et la retry logic.
"""

import logging
import os
from pathlib import Path

from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

from .schema import Rule, EnrichedRule

logger = logging.getLogger(__name__)


class EnrichmentOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    strategie_analyse: str
    strategie_justification: str
    guide_analyse: str


class LLMClient:
    """Client pour enrichissement LLM de règles."""

    def __init__(self):
        """Initialise le client Azure OpenAI et le parser JSON."""
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            deployment_name=os.getenv("AZURE_DEPLOYMENT_INGESTION"),
            model_name="kimi-k2.6",
        )
        self.parser = JsonOutputParser(pydantic_object=EnrichmentOutput)

    def load_prompt(self) -> PromptTemplate:
        """Charge le prompt depuis app/ingestion/prompts/enrich_rule.md."""
        prompt_path = (
            Path(__file__).parent / "prompts" / "enrich_rule.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        return PromptTemplate(
            template=prompt_text,
            input_variables=[
                "intitule",
                "solution",
                "controle",
                "objectifs",
                "tags",
                "phases",
            ],
        )

    def enrich_single_rule(self, rule: Rule) -> EnrichedRule:
        """
        Enrichit une règle via LLM.

        Args:
            rule: Rule à enrichir

        Returns:
            EnrichedRule avec champs d'enrichissement

        Raises:
            ValueError: Si l'enrichissement échoue après 3 tentatives
        """
        prompt = self.load_prompt()

        # Formater le prompt avec les données de la règle
        formatted_prompt = prompt.format(
            intitule=rule.intitule,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=", ".join(rule.objectifs),
            tags=", ".join(rule.tags),
            phases=", ".join(rule.phases),
        )

        # Appeler LLM et parser la réponse
        response = self.llm.invoke(formatted_prompt)
        parsed = self.parser.parse(response.content)

        # Créer EnrichedRule
        enriched = EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
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
            llm_provider="kimi-k2.6",
        )

        return enriched
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestLLMClient::test_enrich_single_rule_success -v
```

Expected: PASS

- [ ] **Step 5: Run ruff check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check --fix app/ingestion/llm_client.py tests/unit/ingestion/test_enrichissement.py
```

Expected: No errors after auto-fix.

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/llm_client.py tests/unit/ingestion/test_enrichissement.py && git commit -m "feat: implement LLMClient with LangChain + Azure integration

- LLMClient class : initializes AzureChatOpenAI + JsonOutputParser
- load_prompt() : reads few-shot prompt from prompts/enrich_rule.md
- enrich_single_rule() : calls LLM and returns EnrichedRule
- EnrichmentOutput : Pydantic model for LLM response validation

Tests:
- test_enrich_single_rule_success : mocks Azure API, verifies EnrichedRule creation

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add Retry Logic to LLMClient

**Files:**
- Modify: `app/ingestion/llm_client.py`
- Modify: `tests/unit/ingestion/test_enrichissement.py`

**Interfaces:**
- Consumes: `enrich_single_rule()` (from Task 5)
- Produces: same interface, but with automatic retry on timeout/error (3 attempts, backoff 2s/4s/8s)

- [ ] **Step 1: Write failing test for retry logic**

Add to `tests/unit/ingestion/test_enrichissement.py`:

```python
    @patch("app.ingestion.llm_client.time.sleep")  # Mock sleep to speed up test
    @patch("app.ingestion.llm_client.AzureChatOpenAI")
    def test_enrich_single_rule_retry_on_timeout(self, mock_azure_llm, mock_sleep):
        """Réessaie après timeout, puis réussit."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        # First 2 attempts timeout, 3rd succeeds
        mock_response_success = MagicMock()
        mock_response_success.content = '{"strategie_analyse": "statique", "strategie_justification": "Test", "guide_analyse": "Test guide"}'

        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            mock_response_success,
        ]

        with patch("app.ingestion.llm_client.JsonOutputParser") as mock_parser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse.return_value = {
                "strategie_analyse": "statique",
                "strategie_justification": "Test",
                "guide_analyse": "Test guide",
            }
            mock_parser.return_value = mock_parser_instance

            client = LLMClient()
            rule = Rule(
                id=1, number=1,
                intitule="Test Rule",
                solution="Test solution",
                controle="Test control",
                objectifs=["Obj"],
                tags=["Tag"],
                phases=["Phase"],
                slug="test"
            )

            enriched = client.enrich_single_rule(rule)

            # Verify retries happened
            assert mock_llm_instance.invoke.call_count == 3
            # Verify sleeps (2s, 4s)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)
            # Verify enrichment succeeded
            assert enriched.strategie_analyse == "statique"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestLLMClient::test_enrich_single_rule_retry_on_timeout -v
```

Expected: FAIL (no retry logic implemented yet)

- [ ] **Step 3: Add retry logic to LLMClient.enrich_single_rule()**

Modify `app/ingestion/llm_client.py` - import time module and add retry decorator:

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential
```

Replace the `enrich_single_rule` method with:

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    def enrich_single_rule(self, rule: Rule) -> EnrichedRule:
        """
        Enrichit une règle via LLM avec retry logic.

        Retente automatiquement jusqu'à 3 fois en cas d'erreur timeout,
        avec backoff exponentiel (2s, 4s, 8s).

        Args:
            rule: Rule à enrichir

        Returns:
            EnrichedRule avec champs d'enrichissement

        Raises:
            ValueError: Si l'enrichissement échoue après 3 tentatives
        """
        prompt = self.load_prompt()

        # Formater le prompt avec les données de la règle
        formatted_prompt = prompt.format(
            intitule=rule.intitule,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=", ".join(rule.objectifs),
            tags=", ".join(rule.tags),
            phases=", ".join(rule.phases),
        )

        # Appeler LLM et parser la réponse
        response = self.llm.invoke(formatted_prompt)
        parsed = self.parser.parse(response.content)

        # Créer EnrichedRule
        enriched = EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
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
            llm_provider="kimi-k2.6",
        )

        return enriched
```

- [ ] **Step 4: Add tenacity to pyproject.toml**

Update `dependencies` list in `pyproject.toml` to add `tenacity`:

```python
dependencies = [
    "alembic>=1.18.5",
    "beautifulsoup4>=4.12.2",
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "pgvector>=0.5.0",
    "psycopg2-binary>=2.9.12",
    "pydantic>=2.13.4",
    "python-dotenv>=1.2.2",
    "requests>=2.34.2",
    "sqlalchemy>=2.0.51",
    "tenacity>=8.2.0",
]
```

- [ ] **Step 5: Run uv sync**

```bash
cd /media/david/projets/QualiCheck && uv sync
```

- [ ] **Step 6: Run retry test**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestLLMClient::test_enrich_single_rule_retry_on_timeout -v
```

Expected: PASS

- [ ] **Step 7: Run all LLMClient tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestLLMClient -v
```

Expected: Both tests pass

- [ ] **Step 8: Commit**

```bash
git add app/ingestion/llm_client.py pyproject.toml uv.lock tests/unit/ingestion/test_enrichissement.py && git commit -m "feat: add retry logic to LLMClient with exponential backoff

- Use tenacity @retry decorator : 3 attempts, exponential backoff (2s, 4s, 8s)
- Automatic retry on TimeoutError and other exceptions
- tenacity>=8.2.0 added to dependencies

Tests:
- test_enrich_single_rule_retry_on_timeout : verifies retry behavior with mocked timeouts

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Create enrich_rules() Orchestration Function

**Files:**
- Create: `app/ingestion/enrichissement.py`
- Modify: `tests/unit/ingestion/test_enrichissement.py`

**Interfaces:**
- Consumes: `Rules`, `LLMClient`, logging
- Produces: `enrich_rules(rules: Rules) -> EnrichedRules`

- [ ] **Step 1: Write failing test for enrich_rules()**

Add to `tests/unit/ingestion/test_enrichissement.py`:

```python
from app.ingestion.agregation import Rules, EnrichedRules
from app.ingestion.enrichissement import enrich_rules


class TestEnrichRules:
    """Tests de la fonction orchestration enrich_rules()."""

    @patch("app.ingestion.enrichissement.LLMClient")
    def test_enrich_rules_transforms_collection(self, mock_llm_client_class):
        """Transforme une collection Rules en EnrichedRules."""
        # Setup
        rule1 = Rule(
            id=1, number=1,
            intitule="Rule 1",
            solution="Sol 1",
            controle="Ctrl 1",
            objectifs=["Obj1"],
            tags=["Tag1"],
            phases=["Phase1"],
            slug="rule-1"
        )
        rule2 = Rule(
            id=2, number=2,
            intitule="Rule 2",
            solution="Sol 2",
            controle="Ctrl 2",
            objectifs=["Obj2"],
            tags=["Tag2"],
            phases=["Phase2"],
            slug="rule-2"
        )
        rules = Rules([rule1, rule2])

        # Mock LLMClient
        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1, number=1, intitule="Rule 1", solution="Sol 1", controle="Ctrl 1",
            objectifs=["Obj1"], tags=["Tag1"], phases=["Phase1"], slug="rule-1",
            strategie_analyse="statique",
            strategie_justification="Expl 1",
            guide_analyse="Guide 1"
        )
        enriched2 = EnrichedRule(
            id=2, number=2, intitule="Rule 2", solution="Sol 2", controle="Ctrl 2",
            objectifs=["Obj2"], tags=["Tag2"], phases=["Phase2"], slug="rule-2",
            strategie_analyse="playwright",
            strategie_justification="Expl 2",
            guide_analyse="Guide 2"
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        # Execute
        enriched_rules = enrich_rules(rules)

        # Assert
        assert isinstance(enriched_rules, EnrichedRules)
        assert len(enriched_rules.enriched_rules) == 2
        assert enriched_rules.enriched_rules[0].strategie_analyse == "statique"
        assert enriched_rules.enriched_rules[1].strategie_analyse == "playwright"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestEnrichRules::test_enrich_rules_transforms_collection -v
```

Expected: FAIL (module doesn't exist)

- [ ] **Step 3: Create enrichissement.py with enrich_rules()**

Create `app/ingestion/enrichissement.py`:

```python
"""
Étape 3 — Enrichissement du pipeline d'ingestion.

Transformation de chaque Rule en EnrichedRule via appel LLM (Kimi K2.6).
"""

import logging

from .agregation import Rules, EnrichedRules
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


def enrich_rules(rules: Rules) -> EnrichedRules:
    """
    Enrichit une collection de Rules via LLM.

    Chaque règle est enrichie avec strategie_analyse, strategie_justification,
    et guide_analyse générés par l'agent Kimi K2.6.

    Args:
        rules: Collection Rules validée (Étape 2)

    Returns:
        Collection EnrichedRules avec tous les champs enrichis

    Raises:
        ValueError: Si une règle échoue enrichissement (3 timeouts épuisés)
    """
    llm_client = LLMClient()
    enriched_list = []

    for rule in rules.regles:
        try:
            enriched = llm_client.enrich_single_rule(rule)
            enriched_list.append(enriched)
        except TimeoutError as e:
            logger.error(
                f"Règle {rule.number} — enrichissement : KO (3 timeouts)"
            )
            raise ValueError(
                f"Enrichissement échoué pour règle {rule.number}"
            ) from e
        except Exception as e:
            logger.error(f"Règle {rule.number} — enrichissement : KO ({e})")
            raise

    enriched_rules = EnrichedRules(enriched_list)
    logger.info(f"Enrichissement : {len(enriched_list)} règles enrichies")
    return enriched_rules
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestEnrichRules::test_enrich_rules_transforms_collection -v
```

Expected: PASS

- [ ] **Step 5: Run ruff check**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check --fix app/ingestion/enrichissement.py
```

- [ ] **Step 6: Run all enrichment tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py -v
```

Expected: All 3 tests pass

- [ ] **Step 7: Commit**

```bash
git add app/ingestion/enrichissement.py tests/unit/ingestion/test_enrichissement.py && git commit -m "feat: implement enrich_rules() orchestration function

- Transforms Rules collection into EnrichedRules
- Iterates over each rule, calls LLMClient.enrich_single_rule()
- Fail-fast on enrichment error (logs error, raises ValueError)
- Summary log on success (X rules enriched)

Tests:
- test_enrich_rules_transforms_collection : verifies Rules → EnrichedRules transformation

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Add Timeout and Error Logging Tests

**Files:**
- Modify: `tests/unit/ingestion/test_enrichissement.py`

**Interfaces:**
- Consumes: `enrich_rules()`, `LLMClient`
- Produces: test cases for timeout logging and critical error handling

- [ ] **Step 1: Write test for timeout logging**

Add to `TestEnrichRules`:

```python
    @patch("app.ingestion.enrichissement.logger")
    @patch("app.ingestion.enrichissement.LLMClient")
    def test_enrich_rules_logs_on_all_timeouts(self, mock_llm_client_class, mock_logger):
        """Logue erreur critique si les 3 tentatives timeout."""
        rule = Rule(
            id=42, number=42,
            intitule="Rule 42",
            solution="Sol",
            controle="Ctrl",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="rule-42"
        )
        rules = Rules([rule])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance
        mock_llm_instance.enrich_single_rule.side_effect = TimeoutError("All retries exhausted")

        try:
            enrich_rules(rules)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Verify error was logged
        mock_logger.error.assert_called()
        call_args = str(mock_logger.error.call_args)
        assert "Règle 42" in call_args or "42" in call_args
        assert "enrichissement" in call_args
        assert "KO" in call_args
```

- [ ] **Step 2: Write test for success logging**

Add to `TestEnrichRules`:

```python
    @patch("app.ingestion.enrichissement.logger")
    @patch("app.ingestion.enrichissement.LLMClient")
    def test_enrich_rules_logs_success_summary(self, mock_llm_client_class, mock_logger):
        """Logue le résumé de succès."""
        rule1 = Rule(
            id=1, number=1, intitule="R1", solution="S1", controle="C1",
            objectifs=["O1"], tags=["T1"], phases=["P1"], slug="r1"
        )
        rule2 = Rule(
            id=2, number=2, intitule="R2", solution="S2", controle="C2",
            objectifs=["O2"], tags=["T2"], phases=["P2"], slug="r2"
        )
        rules = Rules([rule1, rule2])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1, number=1, intitule="R1", solution="S1", controle="C1",
            objectifs=["O1"], tags=["T1"], phases=["P1"], slug="r1",
            strategie_analyse="statique", strategie_justification="X", guide_analyse="Y"
        )
        enriched2 = EnrichedRule(
            id=2, number=2, intitule="R2", solution="S2", controle="C2",
            objectifs=["O2"], tags=["T2"], phases=["P2"], slug="r2",
            strategie_analyse="playwright", strategie_justification="X", guide_analyse="Y"
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        enriched_rules = enrich_rules(rules)

        # Verify success log
        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        assert "Enrichissement" in call_args
        assert "2" in call_args
        assert "règles enrichies" in call_args
```

- [ ] **Step 3: Run logging tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py::TestEnrichRules -v
```

Expected: All 3 tests pass (original + 2 logging tests)

- [ ] **Step 4: Run all enrichment tests**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/test_enrichissement.py -v
```

Expected: 5 tests total pass

- [ ] **Step 5: Commit**

```bash
git add tests/unit/ingestion/test_enrichissement.py && git commit -m "test: add logging tests for enrichment error/success paths

- test_enrich_rules_logs_on_all_timeouts : verify error log on 3 failed attempts
- test_enrich_rules_logs_success_summary : verify success log with rule count

Total: 5 enrichment tests passing

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Lint and Final Tests

**Files:**
- Check: all modified/created files

**Interfaces:**
- Consumes: all implementation
- Produces: clean lint, all tests passing

- [ ] **Step 1: Run ruff check and fix on all ingestion files**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check --fix app/ingestion/ tests/unit/ingestion/
```

- [ ] **Step 2: Run all unit tests for ingestion (Étapes 1, 2, 3)**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ingestion/ -v
```

Expected: 21 tests pass (3 acquisition + 13 agregation + 5 enrichissement)

- [ ] **Step 3: Run entire test suite**

```bash
cd /media/david/projets/QualiCheck && uv run pytest tests/unit/ -v
```

Expected: All unit tests pass

- [ ] **Step 4: Verify no linting issues**

```bash
cd /media/david/projets/QualiCheck && uv run ruff check app/ingestion/ tests/unit/ingestion/
```

Expected: "All checks passed!"

- [ ] **Step 5: Commit if auto-fixes were made**

```bash
git add -A && git commit -m "style: apply ruff auto-fixes to enrichment code

No functional changes, formatting and import organization only.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Update Documentation and CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `TODO_PIPELINE_INGESTION.md`

**Interfaces:**
- Consumes: all tasks completed
- Produces: updated project tracking

- [ ] **Step 1: Update CHANGELOG.md**

Add entry at the top:

```markdown
## 2026-07-19 — Claude Code (Part 2)

- **Étape 3 — Enrichissement (pipeline d'ingestion)** — voir `app/ingestion/enrichissement.py`, `app/ingestion/llm_client.py`, `tests/unit/ingestion/test_enrichissement.py`
  - Classe Pydantic `EnrichedRule` (schema.py) : extension de Rule avec champs enrichissement
  - Classe `EnrichedRules` : collection non-vide d'EnrichedRule
  - Classe `LLMClient` : client LangChain + Azure Kimi K2.6
    - Chargement prompt depuis `prompts/enrich_rule.md` (few-shot)
    - Retry logic : 3 tentatives, backoff exponentiel 2s/4s/8s via tenacity
    - JsonOutputParser pour parsing réponse LLM stricte
  - Fonction `enrich_rules()` : orchestration Rules → EnrichedRules
  - Logging : timeout individuel, erreur critique (3 timeouts), synthèse succès
  - Tests unitaires : 5 tests (réussite, retry, erreur, logging)
  - Dépendances : langchain>=0.1.0, langchain-openai>=0.1.0, tenacity>=8.2.0
  - Convention : code anglais, docs/comments français
```

- [ ] **Step 2: Update TODO_PIPELINE_INGESTION.md**

Find the Étape 3 section and mark it complete:

```markdown
- [x] **Étape 3 — Enrichissement**
  - [x] `app/ingestion/enrichissement.py`
  - [x] Classe `EnrichedRule` (Pydantic) : extension Rule
  - [x] Classe `EnrichedRules` (collection non-vide)
  - [x] Fonction `enrich_rules()` : Rules → EnrichedRules
  - [x] LLMClient avec LangChain + Azure
  - [x] Retry logic (3 tentatives, backoff 2s/4s/8s)
  - [x] Logging : timeout, erreur, synthèse
  - [x] Few-shot prompt dans prompts/enrich_rule.md
  - [x] Tests unitaires (5 tests)
  - Tests passants ✅
```

- [ ] **Step 3: Commit documentation updates**

```bash
git add CHANGELOG.md TODO_PIPELINE_INGESTION.md && git commit -m "docs: update CHANGELOG and TODO for Étape 3 completion

- Étape 3 (Enrichissement) : terminée ✅
- 21 tests passants (3 Étape 1 + 13 Étape 2 + 5 Étape 3)
- Prêt pour Étape 4 (Stockage)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Summary

✅ **Étape 3 — Enrichissement** fully implemented:

- **Models:** `EnrichedRule` (Pydantic extension), `EnrichedRules` (collection)
- **LLM Integration:** `LLMClient` with LangChain chains + Azure + retry logic
- **Orchestration:** `enrich_rules()` function transforming `Rules` → `EnrichedRules`
- **Prompt:** Few-shot examples in `app/ingestion/prompts/enrich_rule.md`
- **Retry:** Automatic 3 attempts with exponential backoff (2s/4s/8s)
- **Logging:** Granular (timeout individual, critical error, success summary)
- **Tests:** 5 unit tests with mocks, no Azure integration tests
- **Tech:** LangChain 0.1.x, tenacity 8.2.x, langchain-openai

**Total tests passing:** 21 (acquisition 3 + agregation 13 + enrichissement 5)
**Lint:** Clean (ruff checks passing)

