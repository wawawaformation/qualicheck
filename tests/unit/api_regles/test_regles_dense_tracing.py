"""
Traçage de POST /regles/dense : les spans du retrieval doivent être des
enfants d'un span racine, pas quatre traces orphelines.
"""

from unittest.mock import MagicMock, patch

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.api_regles.regles import chercher_regles_dense
from app.api_regles.schemas import RegleDenseQuery


def _setup_test_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


@patch("app.retrieval.guardrail.ChatOpenAI")
def test_chercher_regles_dense_regroupe_les_spans_sous_une_racine(mock_llm_class):
    provider, exporter = _setup_test_tracer()
    tracer = provider.get_tracer("test")

    reponse_llm = MagicMock()
    reponse_llm.content = '{"dans_perimetre": false}'
    reponse_llm.usage_metadata = {"input_tokens": 5, "output_tokens": 2}
    mock_llm_class.return_value.invoke.return_value = reponse_llm

    with (
        patch("app.api_regles.regles.get_tracer", return_value=tracer),
        patch("app.retrieval.guardrail.get_tracer", return_value=tracer),
    ):
        resultat = chercher_regles_dense(
            requete=RegleDenseQuery(question="Une question de test ?"),
            session=MagicMock(),
            client_nom="test",
        )

    # Comportement métier inchangé : hors périmètre => liste vide.
    assert resultat == []

    spans = {s.name: s for s in exporter.get_finished_spans()}
    assert "chercher_regles_dense" in spans
    racine, guardrail = spans["chercher_regles_dense"], spans["appel_llm_guardrail"]
    assert racine.parent is None
    assert guardrail.parent.span_id == racine.context.span_id
    assert guardrail.context.trace_id == racine.context.trace_id
