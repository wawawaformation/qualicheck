# A2 — Instrumentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Exception projet QualiCheck** : `~/.claude/CLAUDE.md` (section
> « Optimisation des ressources ») demande un agent unique par défaut une
> fois la conception validée — le recours à des subagents est
> exceptionnel. Pour ce plan, **exécuter en Inline Execution
> (superpowers:executing-plans), pas en mode subagent-driven**, sauf
> demande contraire explicite de David au moment de l'exécution.

**Goal:** Rendre observable chaque appel LLM et chaque appel d'outil de
l'agent US2 (agent nu + retrieval), via des spans OpenTelemetry exportés
soit vers Langfuse Cloud (OTLP), soit dans un fichier JSONL local — et
exposer un `trace_id` dans la réponse HTTP.

**Architecture:** Un module `app/observability/tracing.py` centralise
l'initialisation OpenTelemetry (SDK/API standard, jamais le SDK Langfuse)
et fournit `get_tracer()` + `current_trace_id()`. Les modules existants
(`app/agent_us2/loop.py`, `app/retrieval/decomposition.py`,
`app/retrieval/jugement.py`, `app/retrieval/guardrail.py`,
`app/retrieval/retrieval.py`) s'appuient sur ce module pour ouvrir un
span autour de chaque appel LLM et chaque appel d'outil/recherche dense,
sans changer leur comportement fonctionnel.

**Tech Stack:** `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http` (Python), pytest.

## Global Constraints

- Une trace par appel LLM et par appel d'outil, côté agent (`app/agent_us2/`)
  et côté retrieval (`app/retrieval/`) — pas de granularité plus large
  (décision 1, `A2_instrumentation.md`).
- OpenTelemetry SDK/API uniquement dans le code applicatif — jamais le
  SDK Langfuse directement (décision 2).
- Deux exporteurs possibles, choisis par la variable d'env
  `OTEL_EXPORTER` : `otlp` (vers Langfuse Cloud) ou `jsonl` (fichier
  local `logs/traces_agent_us2.jsonl`, défaut) (décision 2).
- Le texte brut des questions/réponses est autorisé dans les traces pour
  l'instant (pas d'utilisateur réel) — ne pas ajouter de filtrage/masquage
  ici, ce sera le rôle de C2 (décision 3). Ne pas non plus le retirer
  volontairement : les champs `attributs` transportent ce qui existe déjà
  dans les objets applicatifs (question, tokens...), sans traitement
  spécial.
- `QuestionReponse` gagne un champ `trace_id` ; `openapi.json` doit être
  mis à jour et sa version bumpée (décision 4).
- Ne pas dupliquer la logique de retry existante (3 tentatives, backoff
  exponentiel, `tenacity`) déjà présente dans chaque client LLM — le span
  entoure l'appel existant, il ne le remplace pas.
- Tests unitaires uniquement pour cet increment (pas de test
  d'intégration destructeur, donc pas de `POSTGRES_TEST_DB` en jeu ici).

---

## File Structure

- Create: `app/observability/__init__.py` — package vide.
- Create: `app/observability/tracing.py` — initialisation OTel,
  exporteur JSONL maison, `get_tracer()`, `current_trace_id()`.
- Test: `tests/unit/test_tracing.py`
- Modify: `app/agent_us2/loop.py` — span par appel LLM et par appel
  d'outil dans `repondre()`.
- Test: `tests/unit/test_loop_tracing.py`
- Modify: `app/retrieval/decomposition.py`, `app/retrieval/jugement.py`,
  `app/retrieval/guardrail.py` — span autour de `_appeler_llm`.
- Modify: `app/retrieval/retrieval.py` — span autour de la recherche
  dense (`query_top_n_numeros`).
- Test: `tests/unit/test_retrieval_tracing.py`
- Modify: `app/agent_us2/schemas.py` — champ `trace_id` sur
  `QuestionReponse`.
- Modify: `app/agent_us2/loop.py` (`ResultatAgent`) et
  `app/agent_us2/api.py` — propager le `trace_id` de la boucle jusqu'à
  la réponse HTTP.
- Modify: `conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json`
  — champ `trace_id`, version `0.1.0` → `0.2.0`.
- Test: `tests/integration/test_api_trace_id.py`
- Modify: `pyproject.toml` — dépendances `opentelemetry-sdk`,
  `opentelemetry-exporter-otlp-proto-http`.
- Modify: `.env.example` (si présent) / documentation — variables
  `OTEL_EXPORTER`, `OTEL_EXPORTER_OTLP_ENDPOINT`,
  `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_JSONL_PATH`.

---

### Task 1 : module d'observabilité (SDK OTel + exporteur JSONL/OTLP)

Correspond à la sous-tâche Kanboard #19.

**Files:**
- Create: `app/observability/__init__.py`
- Create: `app/observability/tracing.py`
- Test: `tests/unit/test_tracing.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `get_tracer() -> opentelemetry.trace.Tracer`,
  `current_trace_id() -> str | None`, classe `JSONLSpanExporter(path: str)`.

- [ ] **Step 1: Ajouter les dépendances**

```bash
uv add opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

- [ ] **Step 2: Écrire le test qui échoue**

Créer `tests/unit/test_tracing.py` :

```python
import json

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from app.observability.tracing import JSONLSpanExporter


def test_jsonl_exporter_writes_one_line_per_span(tmp_path):
    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("appel_llm_test") as span:
        span.set_attribute("duree_ms", 42)

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    trace_entry = json.loads(lines[0])
    assert trace_entry["name"] == "appel_llm_test"
    assert trace_entry["attributs"]["duree_ms"] == 42
    assert "trace_id" in trace_entry
    assert trace_entry["erreur"] is False


def test_jsonl_exporter_marks_error_status(tmp_path):
    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    from opentelemetry.trace import Status, StatusCode

    with tracer.start_as_current_span("appel_outil_test") as span:
        span.set_status(Status(StatusCode.ERROR, "echec simule"))

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    trace_entry = json.loads(lines[0])
    assert trace_entry["erreur"] is True
```

- [ ] **Step 3: Lancer le test pour vérifier l'échec**

Run: `uv run pytest tests/unit/test_tracing.py -v`
Expected: FAIL avec `ModuleNotFoundError: No module named 'app.observability'`

- [ ] **Step 4: Créer le package et le module**

Créer `app/observability/__init__.py` (fichier vide).

Créer `app/observability/tracing.py` :

```python
"""
Initialisation OpenTelemetry pour l'agent US2 (increment A2). Voir
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/
A2_instrumentation.md — decision 2 : OTel SDK/API standard, jamais le
SDK Langfuse directement, exporteur OTLP (Langfuse Cloud) ou JSONL local
selon OTEL_EXPORTER.
"""

import json
import os
from collections.abc import Sequence
from pathlib import Path

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

SERVICE_NAME = "qualicheck-agent-us2"


class JSONLSpanExporter(SpanExporter):
    """Exporteur local : une ligne JSON par span (decision 2, meme
    structure de donnees que ce qui partirait vers Langfuse)."""

    def __init__(self, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with open(self._path, "a", encoding="utf-8") as f:
            for span in spans:
                f.write(json.dumps(_span_to_dict(span), ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def _span_to_dict(span: ReadableSpan) -> dict:
    duree_ns = (span.end_time or 0) - (span.start_time or 0)
    return {
        "trace_id": format(span.context.trace_id, "032x"),
        "span_id": format(span.context.span_id, "016x"),
        "name": span.name,
        "duree_ms": duree_ns / 1_000_000,
        "attributs": dict(span.attributes or {}),
        "erreur": bool(span.status and span.status.status_code.name != "UNSET" and span.status.status_code.name != "OK"),
    }


def _parse_headers(raw: str) -> dict:
    """Parse le format standard OTEL_EXPORTER_OTLP_HEADERS : 'cle1=val1,cle2=val2'."""
    headers = {}
    for part in raw.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            headers[k.strip()] = v.strip()
    return headers


_provider: TracerProvider | None = None


def setup_tracing() -> TracerProvider:
    """Initialise le TracerProvider une seule fois par process.

    OTEL_EXPORTER=otlp -> export vers Langfuse Cloud (OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_EXPORTER_OTLP_HEADERS pour l'authentification Langfuse).
    OTEL_EXPORTER=jsonl (defaut) -> fichier local (OTEL_JSONL_PATH,
    defaut logs/traces_agent_us2.jsonl).
    """
    global _provider
    if _provider is not None:
        return _provider

    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)

    mode = os.getenv("OTEL_EXPORTER", "jsonl")
    if mode == "otlp":
        exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            headers=_parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif mode == "jsonl":
        path = os.getenv("OTEL_JSONL_PATH", "logs/traces_agent_us2.jsonl")
        provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(path)))
    else:
        raise ValueError(f"OTEL_EXPORTER inconnu : {mode!r} (attendu 'otlp' ou 'jsonl')")

    trace.set_tracer_provider(provider)
    _provider = provider
    return provider


def get_tracer() -> trace.Tracer:
    setup_tracing()
    return trace.get_tracer(SERVICE_NAME)


def current_trace_id() -> str | None:
    """Le trace_id du span courant, ou None hors de tout span (decision 4)."""
    ctx = trace.get_current_span().get_span_context()
    if ctx is None or ctx.trace_id == 0:
        return None
    return format(ctx.trace_id, "032x")
```

- [ ] **Step 5: Lancer le test pour vérifier qu'il passe**

Run: `uv run pytest tests/unit/test_tracing.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add app/observability/ tests/unit/test_tracing.py pyproject.toml uv.lock
git commit -m "feat(observability): add OpenTelemetry tracing module with JSONL/OTLP exporter"
```

---

### Task 2 : instrumenter la boucle agent (appels LLM + appel d'outil)

Correspond à la sous-tâche Kanboard #20.

**Files:**
- Modify: `app/agent_us2/loop.py`
- Test: `tests/unit/test_loop_tracing.py`

**Interfaces:**
- Consumes: `get_tracer()` (Task 1).
- Produces: `ResultatAgent.trace_id: str | None` (nouveau champ, consommé
  par Task 4).

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/unit/test_loop_tracing.py` :

```python
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.agent_us2 import loop


def _setup_test_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_repondre_emits_one_span_per_llm_call_and_tool_call():
    provider, exporter = _setup_test_tracer()

    ai_message_avec_outil = MagicMock()
    ai_message_avec_outil.tool_calls = [{"args": {"mots_cles": "cookies"}, "id": "call_1"}]
    ai_message_avec_outil.usage_metadata = {"input_tokens": 10, "output_tokens": 5}

    ai_message_finale = MagicMock()
    ai_message_finale.tool_calls = []
    ai_message_finale.usage_metadata = {"input_tokens": 8, "output_tokens": 20}
    ai_message_finale.content = "Reponse finale avec regle 42."

    with (
        patch("app.agent_us2.loop.load_config", return_value={
            "llm": {
                "env_var_endpoint": "AZURE_AI_ENDPOINT",
                "env_var_api_key": "AZURE_AI_API_KEY",
                "env_var_deployment": "AZURE_MODEL_GPT_MINI",
                "temperature": 0,
                "prix_entree_par_million": 0.15,
                "prix_sortie_par_million": 0.60,
            },
            "agent_a1": {"max_tours_securite": 10},
        }),
        patch("app.agent_us2.loop._construire_llm") as mock_construire_llm,
        patch("app.agent_us2.loop.rechercher_regles") as mock_outil,
        patch("app.agent_us2.loop.get_tracer", return_value=provider.get_tracer("test")),
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [ai_message_avec_outil, ai_message_finale]
        mock_construire_llm.return_value = mock_llm
        mock_outil.invoke.return_value = '{"resultats": [{"numero": 42, "intitule": "Test"}]}'

        loop.repondre("Question de test")

    spans = exporter.get_finished_spans()
    noms = [s.name for s in spans]
    assert noms.count("appel_llm") == 2
    assert noms.count("appel_outil") == 1

    span_outil = next(s for s in spans if s.name == "appel_outil")
    assert span_outil.attributes["outil"] == "rechercher_regles"
```

- [ ] **Step 2: Lancer le test pour vérifier l'échec**

Run: `uv run pytest tests/unit/test_loop_tracing.py -v`
Expected: FAIL (`AttributeError` ou `ImportError` : `get_tracer` pas
encore importé/utilisé dans `loop.py`, aucun span émis)

- [ ] **Step 3: Modifier `app/agent_us2/loop.py`**

Ajouter l'import (avec les autres imports du module) :

```python
from app.observability.tracing import current_trace_id, get_tracer
```

Remplacer la fonction `repondre` par :

```python
def repondre(question: str) -> ResultatAgent:
    """Répond à une question autonome (pas de mémoire entre questions, A1)."""
    config = load_config()
    config_llm = config["llm"]
    max_tours = config["agent_a1"]["max_tours_securite"]
    tracer = get_tracer()

    llm = _construire_llm(config_llm).bind_tools([rechercher_regles])
    messages: list = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    debut = time.monotonic()
    tokens_entree = tokens_sortie = 0
    regles_citees: dict[int, str] = {}
    ai_message: AIMessage | None = None
    trace_id = None

    for tour in range(1, max_tours + 1):
        with tracer.start_as_current_span("appel_llm", attributes={"tour": tour}) as span:
            if trace_id is None:
                trace_id = current_trace_id()
            ai_message = _appeler_llm(llm, messages)
            usage = ai_message.usage_metadata or {}
            span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
            span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))

        messages.append(ai_message)
        tokens_entree += usage.get("input_tokens", 0)
        tokens_sortie += usage.get("output_tokens", 0)

        if not ai_message.tool_calls:
            break

        for appel in ai_message.tool_calls:
            with tracer.start_as_current_span(
                "appel_outil", attributes={"outil": "rechercher_regles"}
            ) as span:
                resultat_texte = rechercher_regles.invoke(appel["args"])
            messages.append(ToolMessage(content=resultat_texte, tool_call_id=appel["id"]))
            try:
                for r in json.loads(resultat_texte)["resultats"]:
                    regles_citees[r["numero"]] = r["intitule"]
            except (json.JSONDecodeError, KeyError):
                pass
    else:
        return ResultatAgent(
            reponse=(
                f"L'agent n'a pas conclu en {max_tours} tours (filet de "
                "sécurité technique, pas encore le seuil C1)."
            ),
            regles_citees=_trier_regles_citees(regles_citees),
            nb_tours=max_tours,
            duree_s=time.monotonic() - debut,
            tokens_entree=tokens_entree,
            tokens_sortie=tokens_sortie,
            cout_euros_estime=_estimer_cout_euros(config_llm, tokens_entree, tokens_sortie),
            trace_id=trace_id,
        )

    return ResultatAgent(
        reponse=ai_message.content,
        regles_citees=_trier_regles_citees(regles_citees),
        nb_tours=tour,
        duree_s=time.monotonic() - debut,
        tokens_entree=tokens_entree,
        tokens_sortie=tokens_sortie,
        cout_euros_estime=_estimer_cout_euros(config_llm, tokens_entree, tokens_sortie),
        trace_id=trace_id,
    )
```

Ajouter le champ dans `ResultatAgent` (dataclass en tête de fichier) :

```python
@dataclass
class ResultatAgent:
    reponse: str
    regles_citees: list[dict]
    nb_tours: int
    duree_s: float
    tokens_entree: int
    tokens_sortie: int
    cout_euros_estime: float
    trace_id: str | None
```

- [ ] **Step 4: Lancer le test pour vérifier qu'il passe**

Run: `uv run pytest tests/unit/test_loop_tracing.py -v`
Expected: PASS

- [ ] **Step 5: Lancer les tests existants de la boucle pour vérifier l'absence de régression**

Run: `uv run pytest tests/ -k loop -v`
Expected: PASS (les tests A1 existants continuent de passer avec le
nouveau champ `trace_id`)

- [ ] **Step 6: Commit**

```bash
git add app/agent_us2/loop.py tests/unit/test_loop_tracing.py
git commit -m "feat(agent_us2): instrument LLM and tool calls with OpenTelemetry spans"
```

---

### Task 3 : instrumenter le retrieval (décomposition, jugement, garde-fou, recherche dense)

Correspond à la sous-tâche Kanboard #21.

**Files:**
- Modify: `app/retrieval/decomposition.py`
- Modify: `app/retrieval/jugement.py`
- Modify: `app/retrieval/guardrail.py`
- Modify: `app/retrieval/retrieval.py`
- Test: `tests/unit/test_retrieval_tracing.py`

**Interfaces:**
- Consumes: `get_tracer()` (Task 1).
- Produces: rien de nouveau consommé par une tâche suivante — instrumentation
  terminale pour ce increment.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/unit/test_retrieval_tracing.py` :

```python
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.retrieval.decomposition import DecompositionClient


def _setup_test_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_decomposer_emits_one_span_per_llm_call():
    provider, exporter = _setup_test_tracer()

    with (
        patch("app.retrieval.decomposition.load_config", return_value={
            "decomposition": {"env_var": "AZURE_MODEL_GPT_MINI", "temperature": 0}
        }),
        patch("app.retrieval.decomposition.get_tracer", return_value=provider.get_tracer("test")),
        patch.object(DecompositionClient, "_charger_prompt", return_value="prompt"),
    ):
        client = DecompositionClient()
        client.llm = MagicMock()
        reponse = MagicMock()
        reponse.content = '{"sous_questions": ["une question"]}'
        reponse.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        client.llm.invoke.return_value = reponse

        client.decomposer("une question de test")

    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["appel_llm_decomposition"]
```

- [ ] **Step 2: Lancer le test pour vérifier l'échec**

Run: `uv run pytest tests/unit/test_retrieval_tracing.py -v`
Expected: FAIL (aucun span émis, `get_tracer` pas encore importé dans
`decomposition.py`)

- [ ] **Step 3: Modifier `app/retrieval/decomposition.py`**

Ajouter l'import :

```python
from app.observability.tracing import get_tracer
```

Remplacer `_appeler_llm` par :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str) -> list[str]:
        tracer = get_tracer()
        with tracer.start_as_current_span("appel_llm_decomposition") as span:
            prompt = self._charger_prompt(question)
            response = self.llm.invoke(prompt)
            parsed = self.parser.parse(response.content)

            usage = response.usage_metadata or {}
            span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
            span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)

            return parsed["sous_questions"]
```

- [ ] **Step 4: Appliquer le même principe à `app/retrieval/jugement.py`**

Import ajouté, puis `_appeler_llm` :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str, candidats: list[tuple[int, str]]) -> list[int]:
        tracer = get_tracer()
        with tracer.start_as_current_span("appel_llm_jugement") as span:
            prompt = self._construire_prompt(question, candidats)
            response = self.llm.invoke(prompt)
            parsed = self.parser.parse(response.content)

            usage = response.usage_metadata or {}
            span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
            span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)

            return parsed["numeros_pertinents"]
```

- [ ] **Step 5: Appliquer le même principe à `app/retrieval/guardrail.py`**

Import ajouté, puis `_appeler_llm` :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str) -> bool:
        tracer = get_tracer()
        with tracer.start_as_current_span("appel_llm_guardrail") as span:
            prompt = self._construire_prompt(question)
            response = self.llm.invoke(prompt)
            parsed = self.parser.parse(response.content)

            usage = response.usage_metadata or {}
            span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
            span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)

            return parsed["dans_perimetre"]
```

- [ ] **Step 6: Instrumenter la recherche dense dans `app/retrieval/retrieval.py`**

Ajouter l'import et entourer l'appel `query_top_n_numeros` :

```python
from app.observability.tracing import get_tracer

def retrieve(
    session: Session,
    question: str,
    top_n: int,
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> list[tuple[int, float]]:
    tracer = get_tracer()
    sous_questions = decomposition_client.decomposer(question)
    vectors = embedding_client.embed_batch(sous_questions)

    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for sous_question, vector in zip(sous_questions, vectors, strict=True):
        with tracer.start_as_current_span(
            "recherche_dense", attributes={"sous_question": sous_question, "top_n": top_n}
        ) as span:
            resultats = query_top_n_numeros(session, vector, top_n)
            span.set_attribute("nb_resultats", len(resultats))
        for numero, score in resultats:
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score

    return [(numero, meilleurs_scores[numero]) for numero in ordre]
```

- [ ] **Step 7: Lancer le test pour vérifier qu'il passe**

Run: `uv run pytest tests/unit/test_retrieval_tracing.py -v`
Expected: PASS

- [ ] **Step 8: Lancer les tests existants du retrieval pour vérifier l'absence de régression**

Run: `uv run pytest tests/ -k retrieval -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add app/retrieval/decomposition.py app/retrieval/jugement.py app/retrieval/guardrail.py app/retrieval/retrieval.py tests/unit/test_retrieval_tracing.py
git commit -m "feat(retrieval): instrument LLM calls and dense search with OpenTelemetry spans"
```

---

### Task 4 : exposer `trace_id` dans la réponse API

Correspond à la sous-tâche Kanboard #22.

**Files:**
- Modify: `app/agent_us2/schemas.py`
- Modify: `app/agent_us2/api.py`
- Modify: `conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json`
- Test: `tests/integration/test_api_trace_id.py`

**Interfaces:**
- Consumes: `ResultatAgent.trace_id` (Task 2).
- Produces: `QuestionReponse.trace_id: str | None` (fin de chaîne pour ce
  increment).

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/integration/test_api_trace_id.py` :

```python
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.agent_us2.loop import ResultatAgent
from app.agent_us2.main import app

client = TestClient(app)


def test_poser_question_renvoie_un_trace_id():
    resultat = ResultatAgent(
        reponse="Reponse de test, regle 1.",
        regles_citees=[{"numero": 1, "intitule": "Test"}],
        nb_tours=1,
        duree_s=0.1,
        tokens_entree=10,
        tokens_sortie=5,
        cout_euros_estime=0.0001,
        trace_id="abcd1234abcd1234abcd1234abcd1234",
    )

    with patch("app.agent_us2.api.repondre", return_value=resultat):
        response = client.post("/questions", json={"question": "Question de test ?"})

    assert response.status_code == 200
    corps = response.json()
    assert corps["trace_id"] == "abcd1234abcd1234abcd1234abcd1234"
```

- [ ] **Step 2: Lancer le test pour vérifier l'échec**

Run: `uv run pytest tests/integration/test_api_trace_id.py -v`
Expected: FAIL (`KeyError: 'trace_id'` — le champ n'existe pas encore
sur `QuestionReponse`)

- [ ] **Step 3: Modifier `app/agent_us2/schemas.py`**

```python
class QuestionReponse(BaseModel):
    statut: StatutReponse
    reponse: str
    regles_citees: list[RegleCitee]
    trace_id: str | None = None
```

- [ ] **Step 4: Modifier `app/agent_us2/api.py`**

```python
    return QuestionReponse(
        statut=statut,
        reponse=resultat.reponse,
        regles_citees=resultat.regles_citees,
        trace_id=resultat.trace_id,
    )
```

- [ ] **Step 5: Mettre à jour le contrat `openapi.json`**

Dans `conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json` :
- `info.version` : `"0.1.0"` → `"0.2.0"`.
- Dans `components.schemas.QuestionReponse.properties`, ajouter :

```json
"trace_id": {
  "type": "string",
  "nullable": true,
  "description": "Identifiant de trace OpenTelemetry (increment A2). Permet de retrouver le detail de la reponse dans Langfuse ou dans logs/traces_agent_us2.jsonl selon l'exporteur configure."
}
```

- Dans l'exemple de réponse 200 du endpoint `/questions`, ajouter
  `"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"` à l'objet d'exemple
  existant.

- [ ] **Step 6: Lancer le test pour vérifier qu'il passe**

Run: `uv run pytest tests/integration/test_api_trace_id.py -v`
Expected: PASS

- [ ] **Step 7: Lancer toute la suite de tests de l'agent US2 pour vérifier l'absence de régression**

Run: `uv run pytest tests/ -k agent_us2 -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/agent_us2/schemas.py app/agent_us2/api.py conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json tests/integration/test_api_trace_id.py
git commit -m "feat(agent_us2): expose trace_id in POST /questions response"
```

---

## Hors de ce plan (sous-tâche Kanboard #23)

La création du compte/projet Langfuse Cloud (étape manuelle, hors code)
n'est pas couverte ici — elle conditionne uniquement le test manuel en
mode `OTEL_EXPORTER=otlp`, pas le développement (qui fonctionne entièrement
en mode `jsonl` par défaut, sans dépendance réseau).

## Vérification manuelle finale (une fois les 4 tâches faites)

1. `OTEL_EXPORTER=jsonl uv run uvicorn app.agent_us2.main:app` puis
   `curl -X POST localhost:8000/questions -d '{"question": "..."}'`
   -> vérifier `logs/traces_agent_us2.jsonl` contient des lignes
   `appel_llm` / `appel_outil` avec le même `trace_id` que celui renvoyé
   dans la réponse HTTP.
2. Une fois la sous-tâche #23 faite (compte Langfuse) : configurer
   `OTEL_EXPORTER=otlp` + `OTEL_EXPORTER_OTLP_ENDPOINT` +
   `OTEL_EXPORTER_OTLP_HEADERS`, rejouer la même requête, vérifier que la
   trace apparaît dans l'interface Langfuse sous ce `trace_id`.
