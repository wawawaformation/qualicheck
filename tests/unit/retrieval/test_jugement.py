"""
Tests unitaires pour app/retrieval/jugement.py

Teste le jugement LLM de pertinence des candidats — LLM entièrement
mocké, même patron que tests/unit/retrieval/test_decomposition.py.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.jugement import JugementClient


def _mock_response(numeros_pertinents: list[int], input_tokens: int, output_tokens: int):
    response = MagicMock()
    numeros_json = ", ".join(str(n) for n in numeros_pertinents)
    response.content = f'{{"numeros_pertinents": [{numeros_json}]}}'
    response.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return response


class TestJugementClient:
    """Tests du client de jugement."""

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_retient_les_numeros_pertinents(self, mock_llm_class):
        """Les numéros jugés pertinents par le LLM sont retournés."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [12], input_tokens=200, output_tokens=10
        )

        client = JugementClient()
        resultat = client.juger(
            "Question ?", [(12, "Texte de la règle 12"), (45, "Texte de la règle 45")]
        )

        assert resultat == [12]
        assert client.input_tokens == 200
        assert client.output_tokens == 10

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_liste_vide_si_aucun_candidat_pertinent(self, mock_llm_class):
        """Aucun candidat pertinent : liste vide (refus)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [], input_tokens=200, output_tokens=5
        )

        client = JugementClient()
        resultat = client.juger("Question hors sujet ?", [(12, "Texte de la règle 12")])

        assert resultat == []

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_filtre_un_numero_hallucine_hors_du_pool(self, mock_llm_class):
        """Un numéro halluciné par le LLM, absent des candidats fournis, est filtré."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [12, 999], input_tokens=200, output_tokens=10
        )

        client = JugementClient()
        resultat = client.juger("Question ?", [(12, "Texte de la règle 12")])

        assert resultat == [12]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_reessaie_puis_reussit(self, mock_llm_class, mock_sleep):
        """Réessaie après échec, puis réussit (3 tentatives max)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _mock_response([12], input_tokens=200, output_tokens=10),
        ]

        client = JugementClient()
        resultat = client.juger("Question ?", [(12, "Texte de la règle 12")])

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat == [12]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_fail_open_apres_3_echecs(self, mock_llm_class, mock_sleep):
        """Après 3 échecs, retombe sur tous les candidats non filtrés."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = JugementClient()
        resultat = client.juger(
            "Question ?", [(12, "Texte de la règle 12"), (45, "Texte de la règle 45")]
        )

        assert mock_llm_instance.invoke.call_count == 3
        assert resultat == [12, 45]
