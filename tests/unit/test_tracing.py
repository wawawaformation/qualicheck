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
