# Enrichir les spans `appel_llm` avec input / output — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Exception projet QualiCheck** : `~/.claude/CLAUDE.md` (section
> « Optimisation des ressources ») demande un agent unique par défaut une
> fois la conception validée — le recours à des subagents est
> exceptionnel. Pour ce plan, **exécuter en Inline Execution
> (superpowers:executing-plans), pas en mode subagent-driven**, sauf
> demande contraire explicite de David au moment de l'exécution.

**Goal:** Ajouter sur chaque span `appel_llm` les attributs `llm.input` et
`llm.output` (messages et réponse du modèle, JSON structuré et tronqué) pour
rendre visible le dialogue dans Langfuse / le fichier JSONL local.

**Architecture:** Un helper `set_llm_span_io(span, messages, ai_message,
max_len=4000)` dans `app/observability/tracing.py` sérialise et tronque
input/output ; `app/agent_us2/loop.py` l'appelle dans le span `appel_llm`
après chaque invocation LLM. Les tests unitaires couvrent la sérialisation,
la troncature et les cas particuliers (`tool_calls`, `content` vide).

**Tech Stack:** Python, OpenTelemetry SDK, LangChain messages, pytest.

## Global Constraints

- Uniquement le span `appel_llm` dans `app/agent_us2/loop.py` est enrichi
  (pas le span racine `repondre`, pas le span `appel_outil`).
- Le texte brut est autorisé dans les traces pour l'instant — pas de
  masquage ni d'anonymisation (ce sera le rôle de l'incrément C2).
- Pas d'ajout de dépendance externe : `langchain_core` est déjà utilisé.
- `max_len` par défaut = 4000 caractères par attribut (`llm.input` et
  `llm.output` sont tronqués indépendamment).
- Deux attributs booléens `llm.input_truncated` / `llm.output_truncated`
  reflètent l'état.
- Tests unitaires uniquement pour ce changement.

---

## File Structure

- Modify: `app/observability/tracing.py` — ajouter `set_llm_span_io()`.
- Test: `tests/unit/observability/test_tracing.py` — tests du helper.
- Modify: `app/agent_us2/loop.py` — appeler `set_llm_span_io()` dans le
  span `appel_llm`.
- Modify: `CHANGELOG.md` — tracer la réalisation.

---

## Task 1: Ajouter `set_llm_span_io()` dans `app/observability/tracing.py`

**Files:**
- Modify: `app/observability/tracing.py`
- Test: `tests/unit/observability/test_tracing.py`

**Interfaces:**
- Consumes: `opentelemetry.trace.Span`, `langchain_core.messages.BaseMessage`.
- Produces: `set_llm_span_io(span, messages, ai_message, max_len=4000)`.

### Contexte à connaître

Dans `app/agent_us2/loop.py`, les messages sont des instances LangChain :
`SystemMessage`, `HumanMessage`, `AIMessage`, `ToolMessage`. Leur attribut
principal est `content` (str). `AIMessage` expose `tool_calls` sous la forme
`[{"name": ..., "args": ...}]`. `ToolMessage` expose `tool_call_id`.

### Step 1.1 — Ajouter l'import de `Sequence`

Le fichier importe déjà `from collections.abc import Sequence`. Vérifier
qu'il est présent ; il l'est déjà.

### Step 1.2 — Ajouter la fonction `set_llm_span_io`

Modifier `app/observability/tracing.py` juste avant `current_trace_id()` (après
`get_tracer()`). Ajouter :

```python
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage


def _serialize_message(msg: BaseMessage) -> dict[str, Any]:
    """Convertit un message LangChain en dict sérialisable."""
    serialized: dict[str, Any] = {
        "role": msg.type,
        "content": msg.content or "",
    }
    if isinstance(msg, ToolMessage):
        serialized["tool_call_id"] = msg.tool_call_id
    return serialized


def _serialize_ai_message(msg: AIMessage) -> dict[str, Any]:
    """Convertit la réponse AI en dict sérialisable."""
    output: dict[str, Any] = {
        "role": "assistant",
        "content": msg.content or "",
    }
    if msg.tool_calls:
        output["tool_calls"] = [
            {"name": tc.get("name"), "args": tc.get("args")}
            for tc in msg.tool_calls
        ]
    return output


def _truncate_text(text: str, max_len: int) -> tuple[str, bool]:
    """Tronque `text` au milieu en conservant le début et la fin.

    Retourne (texte_tronque, a_ete_tronque). Le marqueur central est
    `[... tronqué ...]` (22 caractères). Si max_len est inférieur à la
    longueur du marqueur + 2 caractères de contexte, on tronque brutalement
    à droite.
    """
    if len(text) <= max_len:
        return text, False

    marker = "[... tronqué ...]"
    if max_len <= len(marker) + 2:
        return text[:max_len], True

    keep = max_len - len(marker)
    head = keep // 2
    tail = keep - head
    return text[:head] + marker + text[-tail:], True


def set_llm_span_io(
    span: trace.Span,
    messages: Sequence[BaseMessage],
    ai_message: AIMessage,
    max_len: int = 4000,
) -> None:
    """Attache input/output LLM au span courant, tronqué si nécessaire.

    - `llm.input` : JSON compact de la liste des messages (role, content,
      tool_call_id pour ToolMessage).
    - `llm.output` : JSON compact de la réponse AI (role, content,
      tool_calls).
    - `llm.input_truncated` / `llm.output_truncated` : booléens.
    """
    input_data = [_serialize_message(m) for m in messages]
    input_json = json.dumps(input_data, ensure_ascii=False, separators=(",", ":"))
    input_truncated_json, input_truncated = _truncate_text(input_json, max_len)

    output_data = _serialize_ai_message(ai_message)
    output_json = json.dumps(output_data, ensure_ascii=False, separators=(",", ":"))
    output_truncated_json, output_truncated = _truncate_text(output_json, max_len)

    span.set_attribute("llm.input", input_truncated_json)
    span.set_attribute("llm.input_truncated", input_truncated)
    span.set_attribute("llm.output", output_truncated_json)
    span.set_attribute("llm.output_truncated", output_truncated)
```

### Step 1.3 — Écrire le test `test_set_llm_span_io_serialise_messages`

Dans `tests/unit/observability/test_tracing.py`, ajouter :

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


def test_set_llm_span_io_serialise_messages():
    """Sérialisation complète des messages en input et de la réponse AI."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    ai_msg = AIMessage(
        content="Je vais chercher les règles.",
        tool_calls=[{"name": "rechercher_regles", "args": {"query": "accessibilite"}}],
    )
    messages = [
        SystemMessage("Tu es un assistant qualité web."),
        HumanMessage("Quelle est la première règle Opquast ?"),
        ai_msg,
        ToolMessage(content='{"resultats": []}', tool_call_id="call_1"),
    ]

    with tracer.start_as_current_span("appel_llm") as span:
        tracing.set_llm_span_io(span, messages, ai_msg)

    assert span.attributes["llm.input_truncated"] is False
    assert span.attributes["llm.output_truncated"] is False

    parsed_input = json.loads(span.attributes["llm.input"])
    assert parsed_input[0] == {"role": "system", "content": "Tu es un assistant qualité web."}
    assert parsed_input[1] == {"role": "human", "content": "Quelle est la première règle Opquast ?"}
    assert parsed_input[2] == {
        "role": "assistant",
        "content": "Je vais chercher les règles.",
        "tool_calls": [{"name": "rechercher_regles", "args": {"query": "accessibilite"}}],
    }
    assert parsed_input[3] == {"role": "tool", "content": '{"resultats": []}', "tool_call_id": "call_1"}

    parsed_output = json.loads(span.attributes["llm.output"])
    assert parsed_output == {
        "role": "assistant",
        "content": "Je vais chercher les règles.",
        "tool_calls": [{"name": "rechercher_regles", "args": {"query": "accessibilite"}}],
    }
```

### Step 1.4 — Écrire le test `test_set_llm_span_io_tronque_input`

Ajouter :

```python
def test_set_llm_span_io_tronque_input():
    """L'input dépassant max_len est tronqué et le booléen est positionné."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    long_content = "x" * 5000
    messages = [HumanMessage(long_content)]
    ai_msg = AIMessage(content="ok")

    with tracer.start_as_current_span("appel_llm") as span:
        tracing.set_llm_span_io(span, messages, ai_msg, max_len=100)

    assert span.attributes["llm.input_truncated"] is True
    assert "[... tronqué ...]" in span.attributes["llm.input"]
    assert len(span.attributes["llm.input"]) <= 100
    assert span.attributes["llm.output_truncated"] is False
```

### Step 1.5 — Écrire le test `test_set_llm_span_io_gere_content_vide`

Ajouter :

```python
def test_set_llm_span_io_gere_content_vide():
    """Un AIMessage avec content vide et tool_calls est sérialisé proprement."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    ai_msg = AIMessage(
        content="",
        tool_calls=[{"name": "rechercher_regles", "args": {"query": "test"}}],
    )
    messages = [HumanMessage("question")]

    with tracer.start_as_current_span("appel_llm") as span:
        tracing.set_llm_span_io(span, messages, ai_msg)

    output = json.loads(span.attributes["llm.output"])
    assert output["content"] == ""
    assert output["tool_calls"] == [{"name": "rechercher_regles", "args": {"query": "test"}}]
```

### Step 1.6 — Lancer les nouveaux tests seuls

```bash
uv run pytest tests/unit/observability/test_tracing.py -v
```

Expected: les 3 nouveaux tests passent, les anciens tests restent verts.

### Step 1.7 — Commit

```bash
git add app/observability/tracing.py tests/unit/observability/test_tracing.py
git commit -m "feat(observability): helper set_llm_span_io avec sérialisation et troncature"
```

---

## Task 2: Appeler `set_llm_span_io()` dans `app/agent_us2/loop.py`

**Files:**
- Modify: `app/agent_us2/loop.py`
- Test: `tests/unit/agent_us2/test_loop.py` (vérifier qu'aucun test ne casse)

**Interfaces:**
- Consumes: `set_llm_span_io()` depuis `app.observability.tracing`.

### Step 2.1 — Importer le helper

Dans `app/agent_us2/loop.py`, modifier l'import existant :

```python
from app.observability.tracing import current_trace_id, get_tracer, set_llm_span_io
```

### Step 2.2 — Appeler le helper dans le span `appel_llm`

Modifier la boucle dans `repondre()` :

```python
for tour in range(1, max_tours + 1):
    with tracer.start_as_current_span("appel_llm", attributes={"tour": tour}) as span:
        ai_message = _appeler_llm(llm, messages)
        set_llm_span_io(span, messages, ai_message)
        usage = ai_message.usage_metadata or {}
        span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
        span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
```

### Step 2.3 — Lancer les tests de la boucle

```bash
uv run pytest tests/unit/agent_us2/test_loop.py -v
```

Expected: tous les tests passent ; le comportement fonctionnel est inchangé.

### Step 2.4 — Commit

```bash
git add app/agent_us2/loop.py
git commit -m "feat(agent_us2): attache input/output LLM au span appel_llm"
```

---

## Task 3: Vérification globale et changelog

**Files:**
- Modify: `CHANGELOG.md`

### Step 3.1 — Vérifier la suite de tests du dossier observability + agent

```bash
uv run pytest tests/unit/observability tests/unit/agent_us2 -v
```

Expected: tous les tests passent.

### Step 3.2 — Vérifier lint/format si applicable

Si le projet dispose d'une cible de lint (ex. `make lint` ou `uv run ruff check app/agent_us2/loop.py app/observability/tracing.py tests/unit/observability/test_tracing.py`), la lancer.

### Step 3.3 — Ajouter une entrée dans `CHANGELOG.md`

Sous la date du jour (`## 2026-09-20 — OpenCode`), ajouter en haut :

```markdown
- **A2 Tâche d'enrichissement des spans LLM (input/output)** — ajout de
  `set_llm_span_io()` dans `app/observability/tracing.py` et appel dans
  `app/agent_us2/loop.py`. Les spans `appel_llm` portent désormais
  `llm.input` et `llm.output` (JSON structuré des messages et de la
  réponse AI, y compris les `tool_calls`), tronqués à 4000 caractères avec
  indicateurs `llm.input_truncated` / `llm.output_truncated`. Tests dans
  `tests/unit/observability/test_tracing.py` — voir
  `docs/superpowers/specs/2026-09-20-enrichir-span-llm-input-output-design.md`.
```

### Step 3.4 — Commit

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): trace l'enrichissement input/output des spans LLM"
```

---

## Self-Review du plan

1. **Spec coverage** :
   - ✅ Contenu structuré (role, content, tool_call_id, tool_calls) → Task 1.2.
   - ✅ Troncature à 4000 caractères avec booléens → Task 1.2 + tests 1.4.
   - ✅ Helper dans `tracing.py` → Task 1.
   - ✅ Appel dans `app/agent_us2/loop.py` → Task 2.
   - ✅ Tests unitaires → Task 1.3, 1.4, 1.5.
   - ✅ Changelog → Task 3.3.

2. **Placeholder scan** : aucun TBD, TODO ou vague description. Chaque step
   contient du code ou une commande exacte.

3. **Type consistency** : `set_llm_span_io(span, messages, ai_message,
   max_len=4000)` est cohérent entre Task 1 et Task 2. Les types LangChain
   utilisés (`BaseMessage`, `AIMessage`, `ToolMessage`) sont ceux du code
   existant.

4. **Risque identifié** : `ai_message.tool_calls` de LangChain est une
   liste de dict avec les clés `"name"` et `"args"`. Si la structure
   change, le helper lève `AttributeError` ou produit des valeurs
   incorrectes. Le test `test_set_llm_span_io_serialise_messages` sert de
   garde-fou. En cas d'échec, adapter `_serialize_ai_message` pour
   supporter `tool_call.name` / `tool_call.args` si nécessaire.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-20-enrichir-span-llm-input-output-implementation.md`.

Two execution options:

1. **Subagent-Driven (recommended by writing-plans, but NOT by project rules)** —
   fresh subagent per task + two-stage review. Use only if explicitly
   requested.

2. **Inline Execution (project default per `~/.claude/CLAUDE.md`)** — execute
   tasks in this session using `superpowers:executing-plans`, batch
   execution with checkpoints.

Which approach?
