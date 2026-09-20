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


@patch("app.retrieval.decomposition.ChatOpenAI")
def test_decomposer_emits_one_span_per_llm_call(mock_llm_class):
    provider, exporter = _setup_test_tracer()

    mock_llm_instance = MagicMock()
    mock_llm_class.return_value = mock_llm_instance

    with (
        patch("app.retrieval.decomposition.load_config", return_value={
            "decomposition": {"env_var": "AZURE_MODEL_GPT_MINI", "temperature": 0}
        }),
        patch("app.retrieval.decomposition.get_tracer", return_value=provider.get_tracer("test")),
        patch.object(DecompositionClient, "_charger_prompt", return_value="prompt"),
    ):
        client = DecompositionClient()
        reponse = MagicMock()
        reponse.content = '{"sous_questions": ["une question"]}'
        reponse.usage_metadata = {"input_tokens": 5, "output_tokens": 3}
        mock_llm_instance.invoke.return_value = reponse
        client.llm = mock_llm_instance

        client.decomposer("une question de test")

    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["appel_llm_decomposition"]
