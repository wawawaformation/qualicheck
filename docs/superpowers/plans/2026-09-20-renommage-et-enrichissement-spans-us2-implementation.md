# Renommage et enrichissement des spans de l'agent US2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Exception projet QualiCheck** : `~/.claude/CLAUDE.md` (section
> « Optimisation des ressources ») demande un agent unique par défaut une
> fois la conception validée — le recours à des subagents est
> exceptionnel. Pour ce plan, **exécuter en Inline Execution
> (superpowers:executing-plans), pas en mode subagent-driven**, sauf
> demande contraire explicite de David au moment de l'exécution.

**Goal:** Renommer les spans de l'agent US2 (`repondre`, `appel_llm`,
`appel_outil`) avec le préfixe `questions_libres`, ajouter
`llm.provider`/`llm.model`/`llm.temperature` sur les spans LLM, et ajouter
`outil.input`/`outil.output` structurés et tronqués sur les spans outil.

**Architecture:** La configuration métier du LLM (provider, model,
temperature) est ajoutée dans `app/agent_us2/config.yml`. Le helper
`set_llm_span_io()` gagne les attributs LLM. Un nouveau helper
`set_tool_span_io()` traite les spans outil. `app/agent_us2/loop.py`
applique les deux helpers et renomme les spans. Les tests sont mis à jour
pour refléter les nouveaux noms et les nouveaux attributs.

**Tech Stack:** Python, OpenTelemetry SDK, LangChain messages, pytest.

## Global Constraints

- Noms des spans : `questions_libres`, `questions_libres.appel_llm`,
  `questions_libres.appel_outil` (séparateur `.` pour la sémantique objet).
- `llm.provider`, `llm.model`, `llm.temperature` sont lus depuis
  `config["llm"]` dans `app/agent_us2/loop.py`.
- `outil.input` / `outil.output` sont tronqués à 4000 caractères avec les
  booléens `outil.input_truncated` / `outil.output_truncated`.
- La valeur du `trace_id` dans la réponse API et le comportement fonctionnel
  de `repondre()` ne changent pas.
- Tests unitaires uniquement.

---

## File Structure

- Modify: `app/agent_us2/config.yml` — ajouter `provider` et `model`.
- Modify: `app/observability/tracing.py` — ajouter `set_tool_span_io()` et
  enrichir `set_llm_span_io()` pour les attributs LLM.
- Modify: `app/agent_us2/loop.py` — renommer les spans, appeler les helpers.
- Modify: `tests/unit/observability/test_tracing.py` — tests pour
  `set_tool_span_io()`.
- Modify: `tests/unit/agent_us2/test_loop_tracing.py` — mettre à jour les
  noms de spans et vérifier les nouveaux attributs.
- Modify: `CHANGELOG.md` — tracer la réalisation.

---

## Task 1: Enrichir `config.yml` et le helper `set_llm_span_io()`

**Files:**
- Modify: `app/agent_us2/config.yml`
- Modify: `app/observability/tracing.py`
- Modify: `tests/unit/agent_us2/test_loop_tracing.py` (utilise CONFIG_STUB)
- Test: `tests/unit/observability/test_tracing.py`

**Interfaces:**
- Consumes: `config_llm` dict dans `set_llm_span_io()`.
- Produces: `set_llm_span_io(span, messages, ai_message, config_llm=None, max_len=4000)`.

### Contexte à connaître

`set_llm_span_io()` est appelée dans `app/agent_us2/loop.py` qui possède
déjà `config_llm = config["llm"]`. On va donc pouvoir passer ce dict au
helper pour qu'il enregistre `provider`, `model`, `temperature`.

### Step 1.1 — Ajouter `provider` et `model` dans `config.yml`

Modifier `app/agent_us2/config.yml` :

```yaml
llm:
  provider: azure
  model: gpt-5.4-mini
  env_var_endpoint: AZURE_AI_ENDPOINT
  env_var_api_key: AZURE_AI_API_KEY
  env_var_deployment: AZURE_MODEL_GPT_MINI
  temperature: 0
  ...
```

### Step 1.2 — Modifier `set_llm_span_io()` pour accepter `config_llm`

Dans `app/observability/tracing.py`, modifier la signature et le corps de
`set_llm_span_io()` :

```python
def set_llm_span_io(
    span: trace.Span,
    messages: Sequence[BaseMessage],
    ai_message: AIMessage,
    config_llm: dict[str, Any] | None = None,
    max_len: int = 4000,
) -> None:
    """Attache input/output LLM au span courant, tronqué si nécessaire.

    - `llm.input` : JSON compact de la liste des messages (role, content,
      tool_call_id pour ToolMessage).
    - `llm.output` : JSON compact de la réponse AI (role, content,
      tool_calls).
    - `llm.input_truncated` / `llm.output_truncated` : booléens.
    - `llm.provider` / `llm.model` / `llm.temperature` : config du modèle
      si `config_llm` est fourni.
    """
    input_data = [_serialize_message(m) for m in messages]
    input_json = json.dumps(
        input_data, ensure_ascii=False, separators=(",", ":"), default=_json_default
    )
    input_truncated_json, input_truncated = _truncate_text(input_json, max_len)

    output_data = _serialize_ai_message(ai_message)
    output_json = json.dumps(
        output_data, ensure_ascii=False, separators=(",", ":"), default=_json_default
    )
    output_truncated_json, output_truncated = _truncate_text(output_json, max_len)

    span.set_attribute("llm.input", input_truncated_json)
    span.set_attribute("llm.input_truncated", input_truncated)
    span.set_attribute("llm.output", output_truncated_json)
    span.set_attribute("llm.output_truncated", output_truncated)

    if config_llm:
        span.set_attribute("llm.provider", config_llm.get("provider", "unknown"))
        span.set_attribute("llm.model", config_llm.get("model", "unknown"))
        span.set_attribute("llm.temperature", config_llm.get("temperature", 0))
```

### Step 1.3 — Mettre à jour CONFIG_STUB dans `test_loop_tracing.py`

Ajouter `provider` et `model` au stub utilisé par le test de traçage :

```python
"llm": {
    "provider": "azure",
    "model": "gpt-5.4-mini",
    "env_var_endpoint": "AZURE_AI_ENDPOINT",
    ...
}
```

### Step 1.4 — Écrire le test `test_set_llm_span_io_attributs_config_llm`

Dans `tests/unit/observability/test_tracing.py`, ajouter :

```python
def test_set_llm_span_io_attributs_config_llm():
    """Les attributs provider/model/temperature sont enregistrés si fournis."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    ai_msg = AIMessage(content="Réponse.")
    messages = [HumanMessage("question")]
    config_llm = {"provider": "azure", "model": "gpt-5.4-mini", "temperature": 0}

    with tracer.start_as_current_span("appel_llm") as span:
        tracing.set_llm_span_io(span, messages, ai_msg, config_llm=config_llm)

    assert span.attributes["llm.provider"] == "azure"
    assert span.attributes["llm.model"] == "gpt-5.4-mini"
    assert span.attributes["llm.temperature"] == 0
```

### Step 1.5 — Lancer les tests

```bash
uv run pytest tests/unit/observability/test_tracing.py tests/unit/agent_us2/test_loop_tracing.py -v
```

Expected: `test_set_llm_span_io_attributs_config_llm` passe ; les tests
existants restent verts (sauf ceux qui dépendent du nom de span, corrigés
plus tard).

### Step 1.6 — Commit

```bash
git add app/agent_us2/config.yml app/observability/tracing.py tests/unit/observability/test_tracing.py tests/unit/agent_us2/test_loop_tracing.py
git commit -m "feat(observability): ajoute provider/model/temperature aux spans LLM"
```

---

## Task 2: Ajouter `set_tool_span_io()` dans `tracing.py` avec tests

**Files:**
- Modify: `app/observability/tracing.py`
- Test: `tests/unit/observability/test_tracing.py`

**Interfaces:**
- Consumes: `opentelemetry.trace.Span`, dict d'input, texte d'output.
- Produces: `set_tool_span_io(span, tool_input, tool_output, max_len=4000)`.

### Step 2.1 — Ajouter `set_tool_span_io()` dans `app/observability/tracing.py`

Juste après `set_llm_span_io()`, ajouter :

```python
def set_tool_span_io(
    span: trace.Span,
    tool_input: dict[str, Any],
    tool_output: str,
    max_len: int = 4000,
) -> None:
    """Attache input/output outil au span courant, tronqué si nécessaire.

    - `outil.input` : JSON compact des arguments de l'outil.
    - `outil.output` : texte JSON retourné par l'outil.
    - `outil.input_truncated` / `outil.output_truncated` : booléens.
    """
    input_json = json.dumps(
        tool_input, ensure_ascii=False, separators=(",", ":"), default=_json_default
    )
    input_truncated_json, input_truncated = _truncate_text(input_json, max_len)

    output_truncated_json, output_truncated = _truncate_text(tool_output, max_len)

    span.set_attribute("outil.input", input_truncated_json)
    span.set_attribute("outil.input_truncated", input_truncated)
    span.set_attribute("outil.output", output_truncated_json)
    span.set_attribute("outil.output_truncated", output_truncated)
```

### Step 2.2 — Écrire les tests

Dans `tests/unit/observability/test_tracing.py` :

```python
def test_set_tool_span_io_serialise_input_output():
    """Sérialisation des arguments et du résultat d'un outil."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("appel_outil") as span:
        tracing.set_tool_span_io(
            span,
            tool_input={"mots_cles": "prix TTC"},
            tool_output='{"resultats": [{"numero": 56}]}',
        )

    assert span.attributes["outil.input_truncated"] is False
    assert span.attributes["outil.output_truncated"] is False
    assert json.loads(span.attributes["outil.input"]) == {"mots_cles": "prix TTC"}
    assert json.loads(span.attributes["outil.output"]) == {"resultats": [{"numero": 56}]}


def test_set_tool_span_io_tronque_output():
    """La sortie outil dépassant max_len est tronquée."""
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    tracer = provider.get_tracer("test")

    long_output = "x" * 5000

    with tracer.start_as_current_span("appel_outil") as span:
        tracing.set_tool_span_io(span, tool_input={}, tool_output=long_output, max_len=100)

    assert span.attributes["outil.output_truncated"] is True
    assert "[... tronqué ...]" in span.attributes["outil.output"]
    assert len(span.attributes["outil.output"]) <= 100
    assert span.attributes["outil.input_truncated"] is False
```

### Step 2.3 — Lancer les tests

```bash
uv run pytest tests/unit/observability/test_tracing.py -v
```

Expected: les 2 nouveaux tests passent, les anciens restent verts.

### Step 2.4 — Commit

```bash
git add app/observability/tracing.py tests/unit/observability/test_tracing.py
git commit -m "feat(observability): ajoute set_tool_span_io pour input/output outil"
```

---

## Task 3: Renommer les spans et appeler les helpers dans `loop.py`

**Files:**
- Modify: `app/agent_us2/loop.py`
- Modify: `tests/unit/agent_us2/test_loop_tracing.py`
- Modify: `tests/unit/agent_us2/test_loop.py` (si nécessaire)

**Interfaces:**
- Consumes: `set_llm_span_io(span, messages, ai_message, config_llm)`,
  `set_tool_span_io(span, appel["args"], resultat_texte)`.
- Produces: spans renommés avec attributs enrichis.

### Step 3.1 — Importer `set_tool_span_io` dans `loop.py`

Modifier l'import existant :

```python
from app.observability.tracing import current_trace_id, get_tracer, set_llm_span_io, set_tool_span_io
```

### Step 3.2 — Renommer le span racine

```python
with tracer.start_as_current_span("questions_libres"):
```

### Step 3.3 — Renommer le span LLM et enrichir

```python
for tour in range(1, max_tours + 1):
    with tracer.start_as_current_span(
        "questions_libres.appel_llm", attributes={"tour": tour}
    ) as span:
        ai_message = _appeler_llm(llm, messages)
        set_llm_span_io(span, messages, ai_message, config_llm=config_llm)
        usage = ai_message.usage_metadata or {}
        span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
        span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
```

### Step 3.4 — Renommer le span outil et enrichir

```python
for appel in ai_message.tool_calls:
    with tracer.start_as_current_span(
        "questions_libres.appel_outil",
        attributes={"outil": "rechercher_regles"},
    ) as span:
        resultat_texte = rechercher_regles.invoke(appel["args"])
        set_tool_span_io(span, appel["args"], resultat_texte)
    messages.append(ToolMessage(content=resultat_texte, tool_call_id=appel["id"]))
```

### Step 3.5 — Mettre à jour `test_loop_tracing.py`

Remplacer les assertions sur les noms de spans :

```python
assert noms.count("questions_libres.appel_llm") == 2
assert noms.count("questions_libres.appel_outil") == 1
assert any(n == "questions_libres" for n in noms)

span_outil = next(s for s in spans if s.name == "questions_libres.appel_outil")
assert span_outil.attributes["outil"] == "rechercher_regles"
assert "outil.input" in span_outil.attributes
assert "outil.output" in span_outil.attributes

span_llm = next(s for s in spans if s.name == "questions_libres.appel_llm")
assert span_llm.attributes["llm.provider"] == "azure"
assert span_llm.attributes["llm.model"] == "gpt-5.4-mini"
assert "llm.input" in span_llm.attributes
assert "llm.output" in span_llm.attributes
```

### Step 3.6 — Lancer les tests

```bash
uv run pytest tests/unit/agent_us2/test_loop_tracing.py tests/unit/agent_us2/test_loop.py -v
```

Expected: tous les tests passent.

### Step 3.7 — Commit

```bash
git add app/agent_us2/loop.py tests/unit/agent_us2/test_loop_tracing.py tests/unit/agent_us2/test_loop.py
git commit -m "feat(agent_us2): renomme les spans en questions_libres.* et enrichit outil/LLM"
```

---

## Task 4: Vérification globale, lint et changelog

**Files:**
- Modify: `CHANGELOG.md`

### Step 4.1 — Vérifier les tests et le lint

```bash
uv run pytest tests/unit/observability tests/unit/agent_us2 -v
uv run ruff check app/agent_us2/loop.py app/agent_us2/config.yml app/observability/tracing.py tests/unit/observability/test_tracing.py tests/unit/agent_us2/test_loop_tracing.py tests/unit/agent_us2/test_loop.py
```

Expected: tous les tests passent, ruff vert.

### Step 4.2 — Mettre à jour `CHANGELOG.md`

Sous la date du jour, ajouter :

```markdown
- **A2 Suite d'enrichissement des spans US2** — renommage des spans
  `repondre`/`appel_llm`/`appel_outil` en `questions_libres`,
  `questions_libres.appel_llm` et `questions_libres.appel_outil` ; ajout
  de `llm.provider`, `llm.model` et `llm.temperature` sur les spans LLM ;
  ajout de `outil.input` / `outil.output` (tronqués à 4000 caractères)
  sur les spans outil. Mise à jour de `app/agent_us2/config.yml` et des
  tests de traçage — voir
  `docs/superpowers/specs/2026-09-20-renommage-et-enrichissement-spans-us2-design.md`.
```

### Step 4.3 — Commit

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): trace le renommage et enrichissement des spans US2"
```

---

## Self-Review du plan

1. **Spec coverage** :
   - ✅ Renommage spans → Task 3.
   - ✅ `llm.provider`/`llm.model`/`llm.temperature` → Task 1.
   - ✅ `outil.input`/`outil.output` → Task 2 + Task 3.
   - ✅ `config.yml` enrichi → Task 1.
   - ✅ Tests mis à jour → Task 1, 2, 3.
   - ✅ Changelog → Task 4.

2. **Placeholder scan** : aucun TBD, TODO ou vague description. Chaque step
   contient du code ou une commande exacte.

3. **Type consistency** :
   - `set_llm_span_io(..., config_llm=None, ...)` cohérent entre Task 1 et
     Task 3.
   - `set_tool_span_io(span, tool_input, tool_output, max_len=4000)` cohérent
     entre Task 2 et Task 3.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-20-renommage-et-enrichissement-spans-us2-implementation.md`.

Two execution options:

1. **Subagent-Driven (recommended by writing-plans, but NOT by project rules)** —
   fresh subagent per task + two-stage review. Use only if explicitly
   requested.

2. **Inline Execution (project default per `~/.claude/CLAUDE.md`)** — execute
   tasks in this session using `superpowers:executing-plans`, batch
   execution with checkpoints.

Which approach?
