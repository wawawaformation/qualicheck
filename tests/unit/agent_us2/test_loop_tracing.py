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
                "provider": "azure",
                "model": "gpt-5.4-mini",
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

        resultat = loop.repondre("Question de test")

    spans = exporter.get_finished_spans()
    noms = [s.name for s in spans]
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
    assert span_llm.attributes["llm.temperature"] == 0
    assert "llm.input" in span_llm.attributes
    assert "llm.output" in span_llm.attributes

    assert resultat.trace_id is not None
    for span in spans:
        assert format(span.context.trace_id, "032x") == resultat.trace_id
