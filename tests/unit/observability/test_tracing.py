import json

import pytest
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


def test_langfuse_otlp_config_returns_endpoint_and_headers(monkeypatch):
    """Test que _langfuse_otlp_config retourne endpoint et headers corrects."""
    from app.observability.tracing import _langfuse_otlp_config
    import base64

    # Test avec un URL avec trailing slash
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk_test_123")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk_test_456")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com/")

    endpoint, headers = _langfuse_otlp_config()

    # Vérifie que le endpoint est correct et que le trailing slash est supprimé
    assert endpoint == "https://cloud.langfuse.com/api/public/otel"

    # Vérifie que le header Authorization contient le bon base64
    assert "Authorization" in headers
    auth_header = headers["Authorization"]
    assert auth_header.startswith("Basic ")

    # Décode et vérifie le contenu
    decoded = base64.b64decode(auth_header[6:]).decode()
    assert decoded == "pk_test_123:sk_test_456"


def test_langfuse_otlp_config_raises_when_env_var_missing(monkeypatch):
    """Test que _langfuse_otlp_config lève ValueError si une env var manque."""
    from app.observability.tracing import _langfuse_otlp_config

    # Test avec LANGFUSE_PUBLIC_KEY manquant
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk_test_456")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com/")

    with pytest.raises(ValueError) as exc_info:
        _langfuse_otlp_config()
    assert "LANGFUSE_PUBLIC_KEY" in str(exc_info.value)
    assert "LANGFUSE_SECRET_KEY" in str(exc_info.value)
    assert "LANGFUSE_BASE_URL" in str(exc_info.value)
