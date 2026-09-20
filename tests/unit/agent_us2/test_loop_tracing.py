from unittest.mock import MagicMock, patch

import httpx
import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from app.agent_us2 import loop


def _setup_test_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_repondre_emits_one_span_per_llm_call_and_tool_call():
    provider, exporter = _setup_test_tracer()

    ai_message_avec_outil = MagicMock()
    ai_message_avec_outil.tool_calls = [
        {"name": "rechercher_regles", "args": {"mots_cles": "cookies"}, "id": "call_1"}
    ]
    ai_message_avec_outil.usage_metadata = {"input_tokens": 10, "output_tokens": 5}

    mock_outil = MagicMock()
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
        patch.dict("app.agent_us2.loop.OUTILS", {"rechercher_regles": mock_outil}),
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
    assert noms.count("questions_libres.appel_outil.rechercher_regles") == 1
    assert any(n == "questions_libres" for n in noms)

    span_outil = next(
        s for s in spans if s.name == "questions_libres.appel_outil.rechercher_regles"
    )
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


# ---------------------------------------------------------------------------
# A4 — nom du span par outil, et statut du span quand un outil est en panne.
# Vrais outils, seuls le LLM et httpx.get sont remplacés.
# ---------------------------------------------------------------------------

URL_API = "http://localhost:9999"
CONFIG_STUB = {
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
}
REGLE_116 = {"numero": 116, "intitule": "Images décoratives", "solution": "alt vide"}


def _http(statut: int, corps) -> httpx.Response:
    return httpx.Response(statut, json=corps, request=httpx.Request("GET", URL_API))


def _ai(tool_calls: list) -> MagicMock:
    message = MagicMock()
    message.tool_calls = tool_calls
    message.usage_metadata = {"input_tokens": 1, "output_tokens": 1}
    message.content = "Réponse."
    return message


def _repondre_et_recuperer_les_spans(monkeypatch, appels_par_tour: list, reponses_http: list):
    """Joue une question : un tour LLM par élément de appels_par_tour, puis une réponse
    finale ; les appels HTTP des outils reçoivent reponses_http dans l'ordre."""
    provider, exporter = _setup_test_tracer()
    monkeypatch.setattr("app.agent_us2.loop.load_config", lambda: CONFIG_STUB)
    monkeypatch.setattr(
        "app.agent_us2.tools.load_config",
        lambda: {"api_regles": {"env_var_url": "API_REGLES_URL_DEV"}},
    )
    monkeypatch.setenv("API_REGLES_URL_DEV", URL_API)
    monkeypatch.setattr(
        "app.agent_us2.loop.get_tracer", lambda: provider.get_tracer("test")
    )
    llm = MagicMock()
    llm.bind_tools.return_value = llm
    llm.invoke.side_effect = [_ai(appels) for appels in appels_par_tour] + [_ai([])]
    monkeypatch.setattr("app.agent_us2.loop.ChatOpenAI", MagicMock(return_value=llm))

    with patch("app.agent_us2.tools.httpx.get", side_effect=reponses_http):
        loop.repondre("question")
    return exporter.get_finished_spans()


def test_le_span_outil_porte_le_nom_de_loutil_appele(monkeypatch):
    """Casse si deux outils différents produisent des spans indiscernables dans Langfuse."""
    spans = _repondre_et_recuperer_les_spans(
        monkeypatch,
        appels_par_tour=[
            [{"name": "rechercher_regles", "args": {"mots_cles": "images"}, "id": "c1"}],
            [{"name": "lire_regle", "args": {"numero": 116}, "id": "c2"}],
        ],
        reponses_http=[_http(200, [REGLE_116]), _http(200, REGLE_116)],
    )

    par_nom = {s.name: s for s in spans}
    recherche = par_nom["questions_libres.appel_outil.rechercher_regles"]
    lecture = par_nom["questions_libres.appel_outil.lire_regle"]
    assert recherche.attributes["outil"] == "rechercher_regles"
    assert lecture.attributes["outil"] == "lire_regle"


@pytest.mark.parametrize("statut", [500, 503])
def test_une_panne_5xx_met_le_span_outil_en_erreur(monkeypatch, statut):
    """Casse si une panne avalée par l'outil est tracée comme un succès (invisible)."""
    spans = _repondre_et_recuperer_les_spans(
        monkeypatch,
        appels_par_tour=[
            [{"name": "rechercher_regles", "args": {"mots_cles": "images"}, "id": "c1"}]
        ],
        reponses_http=[_http(statut, {"detail": "Service indisponible"})],
    )

    span = next(s for s in spans if s.name == "questions_libres.appel_outil.rechercher_regles")
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["outil.statut"] == statut


def test_une_regle_inconnue_nest_pas_une_erreur_de_span(monkeypatch):
    """Casse si un 404 (résultat métier normal) rougit le span comme une panne."""
    spans = _repondre_et_recuperer_les_spans(
        monkeypatch,
        appels_par_tour=[[{"name": "lire_regle", "args": {"numero": 999}, "id": "c1"}]],
        reponses_http=[_http(404, {"detail": "Règle 999 inconnue"})],
    )

    span = next(s for s in spans if s.name == "questions_libres.appel_outil.lire_regle")
    assert span.status.status_code != StatusCode.ERROR
    assert span.attributes["outil.statut"] == 404


def test_le_span_dun_outil_inconnu_ne_reprend_pas_le_nom_invente(monkeypatch):
    """Casse si un nom inventé par le LLM devient un nom de span : ils prolifèreraient
    dans Langfuse. Le nom demandé reste visible en attribut."""
    spans = _repondre_et_recuperer_les_spans(
        monkeypatch,
        appels_par_tour=[[{"name": "outil_invente_xyz", "args": {}, "id": "c1"}]],
        reponses_http=[],
    )

    assert not any("outil_invente_xyz" in s.name for s in spans)
    span = next(s for s in spans if s.name == "questions_libres.appel_outil.inconnu")
    assert span.attributes["outil"] == "outil_invente_xyz"
    assert span.attributes["outil.statut"] == 404
