"""
Tests unitaires pour app/agent_us2/loop.py

Boucle de l'agent US2 (increment A1) — LLM et outil entièrement mockés,
même patron que tests/unit/retrieval/test_decomposition.py. Un seul LLM
configuré (app/agent_us2/config.yml, clé "llm") : pas de sélection de
candidat au niveau de la boucle.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agent_us2.loop import repondre

CONFIG_STUB = {
    "llm": {
        "env_var_endpoint": "AZURE_AI_ENDPOINT",
        "env_var_api_key": "AZURE_AI_API_KEY",
        "env_var_deployment": "AZURE_MODEL_DEEPSEEK_FLASH",
        "temperature": 0,
        "prix_entree_par_million": 0.15,
        "prix_sortie_par_million": 0.60,
    },
    "agent_a1": {"max_tours_securite": 10},
}


def _ai_message(content: str, tool_calls: list, input_tokens: int, output_tokens: int):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    message.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return message


class TestRepondre:
    """Tests de la boucle repondre()."""

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reponse_directe_sans_appel_outil(self, mock_llm_class, mock_load_config):
        """Le modèle répond directement, sans appeler l'outil — un seul tour."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "Réponse directe.", tool_calls=[], input_tokens=100, output_tokens=20
        )

        resultat = repondre("Une question ?")

        assert resultat.reponse == "Réponse directe."
        assert resultat.nb_tours == 1
        assert resultat.regles_citees == []
        assert resultat.tokens_entree == 100
        assert resultat.tokens_sortie == 20
        # 100 tokens entrée x 0.15 €/M + 20 tokens sortie x 0.60 €/M
        assert resultat.cout_euros_estime == pytest.approx(0.000027)

    @patch("app.agent_us2.loop.rechercher_regles")
    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reponse_apres_appel_outil(self, mock_llm_class, mock_load_config, mock_outil):
        """Le modèle appelle l'outil, obtient un résultat, puis répond."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _ai_message(
                "",
                tool_calls=[
                    {
                        "name": "rechercher_regles",
                        "args": {"mots_cles": "prix TTC"},
                        "id": "call_1",
                    }
                ],
                input_tokens=50,
                output_tokens=10,
            ),
            _ai_message(
                "Le prix doit être TTC (règle 56).",
                tool_calls=[],
                input_tokens=150,
                output_tokens=30,
            ),
        ]
        mock_outil.invoke.return_value = json.dumps(
            {
                "resultats": [{"numero": 56, "intitule": "Prix TTC", "solution": "..."}],
                "total_trouve": 1,
            }
        )

        resultat = repondre("Faut-il le prix TTC ?")

        assert resultat.nb_tours == 2
        assert resultat.regles_citees == [{"numero": 56, "intitule": "Prix TTC"}]
        assert resultat.tokens_entree == 200
        assert resultat.tokens_sortie == 40
        mock_outil.invoke.assert_called_once_with({"mots_cles": "prix TTC"})

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_construit_le_client_avec_temperature_zero(self, mock_llm_class, mock_load_config):
        """Décodage glouton (temperature=0) — même raison que le retrieval."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "ok", tool_calls=[], input_tokens=1, output_tokens=1
        )

        repondre("question")

        assert mock_llm_class.call_args.kwargs["temperature"] == 0

    @patch("app.agent_us2.loop.rechercher_regles")
    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_filet_de_securite_apres_max_tours(
        self, mock_llm_class, mock_load_config, mock_outil
    ):
        """Le modèle appelle l'outil en boucle — filet de sécurité après max_tours_securite."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "",
            tool_calls=[{"name": "rechercher_regles", "args": {"mots_cles": "x"}, "id": "c"}],
            input_tokens=10,
            output_tokens=5,
        )
        mock_outil.invoke.return_value = json.dumps({"resultats": [], "total_trouve": 0})

        resultat = repondre("question sans fin")

        assert resultat.nb_tours == 10
        assert "n'a pas conclu" in resultat.reponse

    @patch("tenacity.nap.time.sleep")
    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reessaie_puis_reussit(self, mock_llm_class, mock_load_config, mock_sleep):
        """Réessaie après échec transitoire, puis réussit (3 tentatives max)."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _ai_message("ok", tool_calls=[], input_tokens=5, output_tokens=5),
        ]

        resultat = repondre("question")

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat.reponse == "ok"
