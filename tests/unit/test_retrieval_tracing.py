from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.retrieval.decomposition import DecompositionClient

load_dotenv()


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
