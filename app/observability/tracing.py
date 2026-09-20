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
