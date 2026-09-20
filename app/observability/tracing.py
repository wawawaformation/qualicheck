"""
Initialisation OpenTelemetry pour l'agent US2 (increment A2). Voir
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/
A2_instrumentation.md — decision 2 : OTel SDK/API standard, jamais le
SDK Langfuse directement, exporteur OTLP (Langfuse Cloud) ou JSONL local
selon OTEL_EXPORTER.
"""

import base64
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
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

logger = logging.getLogger(__name__)

# Nom de service par défaut : chaque point d'entrée (agent US2, API des
# règles) passe le sien à setup_tracing(). Ce défaut ne sert qu'aux appels
# hors serveur (scripts/), où aucun service n'est identifié.
SERVICE_NAME_DEFAUT = "qualicheck"


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
    """Un span au format JSONL.

    `parent_span_id`, les horodatages et le `service_name` sont
    indispensables : sans eux le fichier local est un sac de spans plat, on
    ne peut ni reconstituer l'arbre (quel appel d'outil sous quel
    `repondre`) ni les ordonner, alors que c'est la vue officiellement
    supportée en local (critère C20).
    """
    duree_ns = (span.end_time or 0) - (span.start_time or 0)
    statut = span.status
    code = statut.status_code.name if statut else "UNSET"
    return {
        "trace_id": format(span.context.trace_id, "032x"),
        "span_id": format(span.context.span_id, "016x"),
        "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
        "name": span.name,
        "service_name": (span.resource.attributes.get("service.name") if span.resource else None),
        "start_time": span.start_time,
        "end_time": span.end_time,
        "duree_ms": duree_ns / 1_000_000,
        "attributs": dict(span.attributes or {}),
        "erreur": code not in ("UNSET", "OK"),
        "statut_message": statut.description if statut else None,
    }


def _langfuse_otlp_config() -> tuple[str, dict[str, str]]:
    """Dérive la config OTLP depuis les env vars Langfuse.

    Lit LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY et LANGFUSE_BASE_URL, et
    retourne (endpoint, headers) pour OTLPSpanExporter.
    Lève ValueError si une env var manque.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    base_url = os.getenv("LANGFUSE_BASE_URL", "").strip()

    if not public_key or not secret_key or not base_url:
        raise ValueError(
            "OTEL_EXPORTER=otlp nécessite LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY et LANGFUSE_BASE_URL dans .env"
        )

    # Endpoint du signal "traces" de Langfuse. OTLPSpanExporter(endpoint=...)
    # utilise la valeur telle quelle — il n'ajoute "/v1/traces" que quand
    # l'endpoint vient de la variable générique OTEL_EXPORTER_OTLP_ENDPOINT,
    # ce qui n'est pas notre cas.
    endpoint = base_url.rstrip("/") + "/api/public/otel/v1/traces"

    # Encode public_key:secret_key en base64 pour l'authentification Basic
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {"Authorization": f"Basic {encoded_credentials}"}

    return endpoint, headers


_provider: TracerProvider | None = None


def _build_resource(service_name: str) -> Resource:
    """Identité de l'émetteur des spans.

    `deployment.environment.name` (attribut OTel standard, alimenté par
    APP_ENV, `dev` par défaut) permet de ne pas confondre les traces de dev,
    de test et de production — Langfuse segmente nativement dessus.
    """
    return Resource.create(
        {
            "service.name": service_name,
            "deployment.environment.name": os.getenv("APP_ENV", "dev"),
        }
    )


def setup_tracing(service_name: str = SERVICE_NAME_DEFAUT) -> TracerProvider:
    """Initialise le TracerProvider une seule fois par process.

    Appelé explicitement au démarrage de chaque service, avec son propre
    `service_name` — sinon les spans de l'API des règles se déclareraient
    émis par l'agent.

    OTEL_EXPORTER=otlp -> export vers Langfuse Cloud (LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL pour l'authentification Langfuse).
    OTEL_EXPORTER=jsonl (defaut) -> fichier local (OTEL_JSONL_PATH,
    defaut logs/traces.jsonl).

    Lève ValueError si la configuration est invalide : au démarrage c'est
    volontaire (échouer tôt et bruyamment).
    """
    global _provider
    if _provider is not None:
        return _provider

    provider = TracerProvider(resource=_build_resource(service_name))

    mode = os.getenv("OTEL_EXPORTER", "jsonl")
    if mode == "otlp":
        endpoint, headers = _langfuse_otlp_config()
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif mode == "jsonl":
        path = os.getenv("OTEL_JSONL_PATH", "logs/traces.jsonl")
        provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(path)))
    else:
        raise ValueError(f"OTEL_EXPORTER inconnu : {mode!r} (attendu 'otlp' ou 'jsonl')")

    trace.set_tracer_provider(provider)
    _provider = provider
    return provider


def get_tracer() -> trace.Tracer:
    """Tracer courant, appelé depuis le chemin de requête.

    Ne lève jamais : une observabilité mal configurée doit dégrader la
    trace, pas la réponse à l'utilisateur. En cas d'échec on retombe sur le
    provider par défaut (spans non enregistrés, requête servie normalement).
    """
    try:
        setup_tracing()
    except Exception as e:
        logger.warning("Traçage désactivé — configuration invalide (%s)", e)
    return trace.get_tracer(SERVICE_NAME_DEFAUT)


def _role_message(msg: BaseMessage) -> str:
    """Renvoie le rôle d'un message de manière défensive.

    En production `msg.type` est une chaîne LangChain. Dans les tests
    unitaires, `msg` peut être un `MagicMock` sans `type` défini ; on
    retombe alors sur le nom de la classe concrète.
    """
    role = getattr(msg, "type", None)
    if isinstance(role, str):
        return role
    return type(msg).__name__


def _serialize_message(msg: BaseMessage) -> dict[str, Any]:
    """Convertit un message LangChain en dict sérialisable.

    Les AIMessage de l'historique portent leurs tool_calls et prennent le
    role `assistant` pour la lisibilité dans Langfuse. Les objets mockés
    dans les tests unitaires sont traités de manière dégradée.
    """
    if isinstance(msg, AIMessage) or getattr(msg, "tool_calls", None) is not None:
        return _serialize_ai_message(msg)

    serialized: dict[str, Any] = {
        "role": _role_message(msg),
        "content": getattr(msg, "content", "") or "",
    }
    tool_call_id = getattr(msg, "tool_call_id", None)
    if isinstance(tool_call_id, str):
        serialized["tool_call_id"] = tool_call_id
    return serialized


def _serialize_ai_message(msg: AIMessage) -> dict[str, Any]:
    """Convertit la réponse AI en dict sérialisable.

    Accepte aussi les objets mockés en test : les valeurs non dict sont
    ignorées, content absent est traité comme vide.
    """
    output: dict[str, Any] = {
        "role": "assistant",
        "content": getattr(msg, "content", "") or "",
    }
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        output["tool_calls"] = [
            {"name": tc.get("name"), "args": tc.get("args")}
            for tc in tool_calls
            if isinstance(tc, dict)
        ]
    return output


def _json_default(obj: Any) -> Any:
    """Fallback de sérialisation JSON pour les objets non natifs.

    En production les messages sont des objets LangChain sérialisables. En
    test, certains champs peuvent être des MagicMock : on les convertit en
    chaîne plutôt que de faire échouer l'export de toute la trace.
    """
    # MagicMock et objets similaires n'ont pas de représentation JSON standard.
    if "Mock" in type(obj).__name__:
        return repr(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


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


def current_trace_id() -> str | None:
    """Le trace_id du span courant, ou None hors de tout span (decision 4)."""
    ctx = trace.get_current_span().get_span_context()
    if ctx.trace_id == 0:
        return None
    return format(ctx.trace_id, "032x")
