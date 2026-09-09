"""
Tests unitaires pour app/retrieval/decomposition.py

Teste la décomposition LLM d'une question en sous-questions — LLM
entièrement mocké, même patron que tests/unit/ingestion/test_enrichment.py.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.decomposition import DecompositionClient


def _mock_response(sous_questions: list[str], input_tokens: int, output_tokens: int):
    response = MagicMock()
    questions_json = ", ".join(f'"{q}"' for q in sous_questions)
    response.content = f'{{"sous_questions": [{questions_json}]}}'
    response.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return response


class TestDecompositionClient:
    """Tests du client de décomposition."""

    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_question_mono_sujet_retourne_liste_a_un_element(self, mock_llm_class):
        """Une question mono-sujet est retournée telle quelle, seule dans la liste."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            ["Chaque image porteuse d'information a-t-elle une alternative textuelle ?"],
            input_tokens=80,
            output_tokens=20,
        )

        client = DecompositionClient()
        resultat = client.decomposer(
            "Chaque image porteuse d'information a-t-elle une alternative textuelle ?"
        )

        assert resultat == [
            "Chaque image porteuse d'information a-t-elle une alternative textuelle ?"
        ]
        assert client.input_tokens == 80
        assert client.output_tokens == 20

    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_question_multi_sujets_retourne_n_sous_questions(self, mock_llm_class):
        """Une question multi-sujets est découpée en plusieurs sous-questions."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [
                "Sur mobile, faut-il des boutons assez grands ?",
                "Faut-il laisser l'utilisateur agrandir la page ?",
            ],
            input_tokens=90,
            output_tokens=40,
        )

        client = DecompositionClient()
        resultat = client.decomposer(
            "Sur mobile, faut-il des boutons assez grands et laisser "
            "l'utilisateur agrandir la page ?"
        )

        assert resultat == [
            "Sur mobile, faut-il des boutons assez grands ?",
            "Faut-il laisser l'utilisateur agrandir la page ?",
        ]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_reessaie_puis_reussit(self, mock_llm_class, mock_sleep):
        """Réessaie après échec, puis réussit (3 tentatives max)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _mock_response(["question"], input_tokens=10, output_tokens=5),
        ]

        client = DecompositionClient()
        resultat = client.decomposer("question")

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat == ["question"]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_fail_open_apres_3_echecs(self, mock_llm_class, mock_sleep):
        """Après 3 échecs, retombe sur [question] plutôt que de lever une exception."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = DecompositionClient()
        resultat = client.decomposer("Ma question originale ?")

        assert mock_llm_instance.invoke.call_count == 3
        assert resultat == ["Ma question originale ?"]
