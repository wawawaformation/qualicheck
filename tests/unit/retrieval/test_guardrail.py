"""
Tests unitaires pour app/retrieval/guardrail.py

Teste la classification LLM dans/hors périmètre — LLM entièrement mocké,
même patron que tests/unit/retrieval/test_jugement.py.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.guardrail import GuardrailClient


def _mock_response(dans_perimetre: bool, input_tokens: int, output_tokens: int):
    response = MagicMock()
    valeur = "true" if dans_perimetre else "false"
    response.content = f'{{"dans_perimetre": {valeur}}}'
    response.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return response


class TestGuardrailClient:
    """Tests du client de classification de périmètre."""

    @patch("app.retrieval.guardrail.ChatOpenAI")
    def test_est_dans_le_perimetre_question_pertinente(self, mock_llm_class):
        """Une question sur une règle de qualité web est classée dans le périmètre."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            True, input_tokens=100, output_tokens=5
        )

        client = GuardrailClient()
        resultat = client.est_dans_le_perimetre(
            "Chaque image porteuse d'information a-t-elle une alternative textuelle ?"
        )

        assert resultat is True
        assert client.input_tokens == 100
        assert client.output_tokens == 5

    @patch("app.retrieval.guardrail.ChatOpenAI")
    def test_est_dans_le_perimetre_question_hors_sujet(self, mock_llm_class):
        """Une question hors sujet est classée hors périmètre."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            False, input_tokens=100, output_tokens=5
        )

        client = GuardrailClient()
        resultat = client.est_dans_le_perimetre("Quelle est la meilleure recette de tarte ?")

        assert resultat is False

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.guardrail.ChatOpenAI")
    def test_est_dans_le_perimetre_reessaie_puis_reussit(self, mock_llm_class, mock_sleep):
        """Réessaie après échec, puis réussit (3 tentatives max)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _mock_response(True, input_tokens=100, output_tokens=5),
        ]

        client = GuardrailClient()
        resultat = client.est_dans_le_perimetre("Question ?")

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat is True

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.guardrail.ChatOpenAI")
    def test_est_dans_le_perimetre_fail_open_apres_3_echecs(self, mock_llm_class, mock_sleep):
        """Après 3 échecs, considère la question dans le périmètre (fail-open)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = GuardrailClient()
        resultat = client.est_dans_le_perimetre("Question ?")

        assert mock_llm_instance.invoke.call_count == 3
        assert resultat is True
