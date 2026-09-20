"""
Test d'intégration de app/agent_us2/loop.repondre() : LLM mocké, mais appel
HTTP réel vers l'API des règles. L'outil recherche_regles parle à une URL
(app/agent_us2/config.yml, api_regles.url), pas à l'objet FastAPI en
mémoire — contrairement à tests/integration/api_regles/, il n'y a pas de
TestClient possible ici, l'agent est un vrai client HTTP externe.

Vérifie le contrat réel entre l'outil et l'API (noms de champs JSON,
format de réponse), pas la logique de la boucle elle-même (déjà couverte,
entièrement mockée, par tests/unit/agent_us2/test_loop.py).

Nécessite l'API des règles réellement démarrée (make api-regles) — lecture
seule sur POSTGRES_DB (GET uniquement, aucune écriture), même principe que
scripts/check_api_regles_acceptance.py pour ses cas GET. Test sauté
automatiquement si l'API n'est pas joignable.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.agent_us2.loop import repondre


def _api_disponible() -> bool:
    try:
        httpx.get("http://localhost:8880/regles", params={"q": "test"}, timeout=2)
        return True
    except httpx.ConnectError:
        return False


pytestmark = pytest.mark.skipif(
    not _api_disponible(), reason="API des règles non démarrée (make api-regles)"
)


def _ai_message(content: str, tool_calls: list, input_tokens: int = 10, output_tokens: int = 10):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    message.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return message


@patch("app.agent_us2.loop.ChatOpenAI")
def test_repondre_avec_vrai_appel_api_regles(mock_llm_class):
    """
    L'outil interroge vraiment l'API des règles et les numéros trouvés
    remontent dans regles_citees — pas de contenu figé attendu ici (le
    corpus peut évoluer, cf. carte Kanboard #22), seulement la forme du
    contrat : de vrais numéros de règles reviennent bien de l'appel réel.
    """
    mock_llm_instance = MagicMock()
    mock_llm_class.return_value = mock_llm_instance
    mock_llm_instance.bind_tools.return_value = mock_llm_instance
    mock_llm_instance.invoke.side_effect = [
        _ai_message(
            "",
            tool_calls=[
                {
                    "name": "rechercher_regles",
                    "args": {"mots_cles": "texte alternatif"},
                    "id": "call_1",
                }
            ],
        ),
        _ai_message("Réponse basée sur les règles trouvées.", tool_calls=[]),
    ]

    resultat = repondre("Faut-il un texte alternatif sur les images ?")

    assert resultat.nb_tours == 2
    assert len(resultat.regles_citees) > 0
    assert all(
        isinstance(r["numero"], int) and isinstance(r["intitule"], str)
        for r in resultat.regles_citees
    )


@patch("app.agent_us2.loop.get_tracer")
@patch("app.agent_us2.loop.ChatOpenAI")
def test_repondre_avec_tracing_reel(mock_llm_class, mock_get_tracer):
    """
    Le vrai appel outil (httpx vers l'API des règles, pas un mock) passe
    bien par le wrapper de tracing : un span "appel_outil" est émis pour
    cet appel réel, et tous les spans de la requête partagent le même
    trace_id, retrouvé dans resultat.trace_id — même invariant que
    tests/unit/test_loop_tracing.py, mais exercé ici sur un vrai
    aller-retour réseau plutôt qu'un outil mocké.
    """
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    mock_get_tracer.return_value = provider.get_tracer("test")

    mock_llm_instance = MagicMock()
    mock_llm_class.return_value = mock_llm_instance
    mock_llm_instance.bind_tools.return_value = mock_llm_instance
    mock_llm_instance.invoke.side_effect = [
        _ai_message(
            "",
            tool_calls=[
                {
                    "name": "rechercher_regles",
                    "args": {"mots_cles": "texte alternatif"},
                    "id": "call_1",
                }
            ],
        ),
        _ai_message("Réponse basée sur les règles trouvées.", tool_calls=[]),
    ]

    resultat = repondre("Faut-il un texte alternatif sur les images ?")

    spans = exporter.get_finished_spans()
    noms = [s.name for s in spans]
    assert "appel_outil" in noms

    assert resultat.trace_id is not None
    for span in spans:
        assert format(span.context.trace_id, "032x") == resultat.trace_id
