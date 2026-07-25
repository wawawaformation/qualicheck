"""
Tests unitaires pour app/ingestion/enrichment.py et app/ingestion/llm_client.py

Teste l'enrichissement LLM de règles avec retry logic et parsing JSON.
"""

from unittest.mock import MagicMock, patch

from app.ingestion.aggregation import EnrichedRules, Rules
from app.ingestion.enrichment import enrich_rules
from app.ingestion.llm_client import LLMClient
from app.ingestion.schema import EnrichedRule
from app.ingestion.schema import RuleAggregation as Rule


class TestLLMClient:
    """Tests du client LangChain + Azure."""

    @patch("app.ingestion.llm_client.ChatOpenAI")
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
        mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=1,
            number=1,
            intitule="Les images ont un attribut alt",
            theme="Images et médias",
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
        assert enriched.llm_model == "kimi-k2.6"
        assert enriched.prompt_version == 4
        assert client.input_tokens == 100
        assert client.output_tokens == 50

    @patch("tenacity.nap.time.sleep")
    @patch("app.ingestion.llm_client.ChatOpenAI")
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
        mock_response_success.usage_metadata = {"input_tokens": 10, "output_tokens": 5}

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
            theme="Contenus",
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
    @patch("app.ingestion.llm_client.ChatOpenAI")
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
            theme="Contenus",
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


class TestEnrichRules:
    """Tests de la fonction orchestration enrich_rules()."""

    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_transforms_collection(self, mock_llm_client_class):
        """Transforme une collection Rules en EnrichedRules."""
        rule1 = Rule(
            id=1,
            number=1,
            intitule="Rule 1",
            theme="Contenus",
            solution="Sol 1",
            controle="Ctrl 1",
            objectifs=["Obj1"],
            tags=["Tag1"],
            phases=["Phase1"],
            slug="rule-1",
        )
        rule2 = Rule(
            id=2,
            number=2,
            intitule="Rule 2",
            theme="Navigation",
            solution="Sol 2",
            controle="Ctrl 2",
            objectifs=["Obj2"],
            tags=["Tag2"],
            phases=["Phase2"],
            slug="rule-2",
        )
        rules = Rules([rule1, rule2])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1,
            number=1,
            intitule="Rule 1",
            theme="Contenus",
            solution="Sol 1",
            controle="Ctrl 1",
            objectifs=["Obj1"],
            tags=["Tag1"],
            phases=["Phase1"],
            slug="rule-1",
            strategie_analyse="statique",
            strategie_justification="Expl 1",
            guide_analyse="Guide 1",
        )
        enriched2 = EnrichedRule(
            id=2,
            number=2,
            intitule="Rule 2",
            theme="Navigation",
            solution="Sol 2",
            controle="Ctrl 2",
            objectifs=["Obj2"],
            tags=["Tag2"],
            phases=["Phase2"],
            slug="rule-2",
            strategie_analyse="playwright",
            strategie_justification="Expl 2",
            guide_analyse="Guide 2",
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        enriched_rules = enrich_rules(rules)

        assert isinstance(enriched_rules, EnrichedRules)
        assert len(enriched_rules.enriched_rules) == 2
        assert enriched_rules.enriched_rules[0].strategie_analyse == "statique"
        assert enriched_rules.enriched_rules[1].strategie_analyse == "playwright"

    @patch("app.ingestion.enrichment.logger")
    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_logs_on_all_timeouts(self, mock_llm_client_class, mock_logger):
        """Logue erreur critique si les 3 tentatives timeout."""
        rule = Rule(
            id=42,
            number=42,
            intitule="Rule 42",
            theme="Contenus",
            solution="Sol",
            controle="Ctrl",
            objectifs=["Obj"],
            tags=["Tag"],
            phases=["Phase"],
            slug="rule-42",
        )
        rules = Rules([rule])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance
        mock_llm_instance.enrich_single_rule.side_effect = TimeoutError(
            "All retries exhausted"
        )

        try:
            enrich_rules(rules)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass

        mock_logger.error.assert_called()
        call_args = str(mock_logger.error.call_args)
        assert "42" in call_args
        assert "enrichissement" in call_args
        assert "KO" in call_args

    @patch("app.ingestion.enrichment.logger")
    @patch("app.ingestion.enrichment.LLMClient")
    def test_enrich_rules_logs_success_summary(self, mock_llm_client_class, mock_logger):
        """Logue le résumé de succès."""
        rule1 = Rule(
            id=1,
            number=1,
            intitule="R1",
            theme="Contenus",
            solution="S1",
            controle="C1",
            objectifs=["O1"],
            tags=["T1"],
            phases=["P1"],
            slug="r1",
        )
        rule2 = Rule(
            id=2,
            number=2,
            intitule="R2",
            theme="Navigation",
            solution="S2",
            controle="C2",
            objectifs=["O2"],
            tags=["T2"],
            phases=["P2"],
            slug="r2",
        )
        rules = Rules([rule1, rule2])

        mock_llm_instance = MagicMock()
        mock_llm_client_class.return_value = mock_llm_instance

        enriched1 = EnrichedRule(
            id=1,
            number=1,
            intitule="R1",
            theme="Contenus",
            solution="S1",
            controle="C1",
            objectifs=["O1"],
            tags=["T1"],
            phases=["P1"],
            slug="r1",
            strategie_analyse="statique",
            strategie_justification="X",
            guide_analyse="Y",
        )
        enriched2 = EnrichedRule(
            id=2,
            number=2,
            intitule="R2",
            theme="Navigation",
            solution="S2",
            controle="C2",
            objectifs=["O2"],
            tags=["T2"],
            phases=["P2"],
            slug="r2",
            strategie_analyse="playwright",
            strategie_justification="X",
            guide_analyse="Y",
        )
        mock_llm_instance.enrich_single_rule.side_effect = [enriched1, enriched2]

        enrich_rules(rules)

        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        assert "Enrichissement" in call_args
        assert "2" in call_args
        assert "règles enrichies" in call_args


class TestLoadPromptContexte:
    """Vérifie que load_prompt injecte le champ contexte."""

    def test_load_prompt_includes_contexte_when_present(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_MODEL_KIMI", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
            contexte="Texte explicatif de la règle",
        )

        prompt = client.load_prompt(rule)

        assert "Texte explicatif de la règle" in prompt
        assert "{contexte}" not in prompt

    def test_load_prompt_handles_missing_contexte(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_MODEL_KIMI", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
        )

        prompt = client.load_prompt(rule)

        assert "(non disponible)" in prompt
        assert "{contexte}" not in prompt


class TestManifestAndPromptVersion:
    """Vérifie la lecture du manifeste et de la version de prompt."""

    def test_load_manifest_reads_enrichissement_role(self):
        from app.ingestion.llm_client import load_manifest

        manifest = load_manifest()

        assert manifest["enrichissement"]["modele"] == "kimi-k2.6"
        assert manifest["enrichissement"]["env_var"] == "AZURE_MODEL_KIMI"

    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 4

    def test_load_prompt_strips_frontmatter_from_llm_input(self, monkeypatch):
        monkeypatch.setenv("AZURE_AI_ENDPOINT", "http://test")
        monkeypatch.setenv("AZURE_AI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_MODEL_KIMI", "test-model")

        from app.ingestion.llm_client import LLMClient
        from app.ingestion.schema import RuleAggregation

        client = LLMClient()
        rule = RuleAggregation(
            id=1, number=1, intitule="Règle test", theme="Thème",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
            slug="regle-test", solution="Solution", controle="Contrôle",
        )

        prompt = client.load_prompt(rule)

        assert "version: 3" not in prompt
        assert prompt.startswith("# Enrichissement de Règles Opquast")

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_llm_model_provenance_independent_of_env_var(self, mock_azure_llm, monkeypatch):
        """llm_model vient du manifeste, pas de la variable d'environnement résolue."""
        monkeypatch.setenv("AZURE_MODEL_KIMI", "un-nom-de-deploiement-quelconque")

        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance
        mock_response = MagicMock()
        mock_response.content = (
            '{"strategie_analyse": "statique", '
            '"strategie_justification": "Test", "guide_analyse": "Test"}'
        )
        mock_response.usage_metadata = {"input_tokens": 1, "output_tokens": 1}
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=1, number=1, intitule="Test", theme="Contenus",
            solution="S", controle="C", objectifs=["O"], tags=["T"],
            phases=["P"], slug="test",
        )

        enriched = client.enrich_single_rule(rule)

        assert enriched.llm_model == "kimi-k2.6"
        _, kwargs = mock_azure_llm.call_args
        assert kwargs["model"] == "un-nom-de-deploiement-quelconque"
