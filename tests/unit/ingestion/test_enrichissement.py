"""
Tests unitaires pour app/ingestion/enrichissement.py et app/ingestion/llm_client.py

Teste l'enrichissement LLM de règles avec retry logic et parsing JSON.
"""

from unittest.mock import MagicMock, patch

from app.ingestion.llm_client import LLMClient
from app.ingestion.schema import EnrichedRule
from app.ingestion.schema import RuleAggregation as Rule


class TestLLMClient:
    """Tests du client LangChain + Azure."""

    @patch("app.ingestion.llm_client.AzureChatOpenAI")
    def test_enrich_single_rule_success(self, mock_azure_llm):
        """Enrichit une règle avec succès."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_response = MagicMock()
        mock_response.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Vérification simple du DOM", '
            '"guide_analyse": "Parcourez toutes les images et vérifiez l\'attribut alt."}'
        )
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Les images ont un attribut alt",
            solution="Ajouter alt descriptif",
            controle="Vérifier alt présent",
            objectifs=["Accessibilité"],
            tags=["HTML"],
            phases=["Intégration"],
            slug="images-alt",
        )

        enriched = client.enrich_single_rule(rule)

        assert isinstance(enriched, EnrichedRule)
        assert enriched.strategie_analyse == "statique"
        assert enriched.strategie_justification == "Vérification simple du DOM"
        assert enriched.guide_analyse == "Parcourez toutes les images et vérifiez l'attribut alt."
        assert enriched.strategie_source == "ia_import"
        assert enriched.llm_provider == "kimi-k2.6"

    @patch("tenacity.nap.time.sleep")
    @patch("app.ingestion.llm_client.AzureChatOpenAI")
    def test_enrich_single_rule_retry_on_timeout(self, mock_azure_llm, mock_sleep):
        """Réessaie après timeout, puis réussit."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_response_success = MagicMock()
        mock_response_success.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Test", '
            '"guide_analyse": "Test guide"}'
        )

        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            mock_response_success,
        ]

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Test Rule",
            solution="Test solution",
            controle="Test control",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="test",
        )

        enriched = client.enrich_single_rule(rule)

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4)
        assert enriched.strategie_analyse == "statique"

    @patch("tenacity.nap.time.sleep")
    @patch("app.ingestion.llm_client.AzureChatOpenAI")
    def test_enrich_single_rule_fails_after_three_timeouts(self, mock_azure_llm, mock_sleep):
        """Lève une exception après 3 tentatives en échec."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance

        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Test Rule",
            solution="Test solution",
            controle="Test control",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="test",
        )

        try:
            client.enrich_single_rule(rule)
            raise AssertionError("Should have raised TimeoutError")
        except TimeoutError:
            pass

        assert mock_llm_instance.invoke.call_count == 3
