"""
Tests unitaires pour app/retrieval/retrieval.py

Teste l'orchestration décomposition → embedding → pgvector → union.
Tous les clients et la session sont mockés.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.retrieval import retrieve


class TestRetrieve:
    """Tests de l'orchestration retrieve()."""

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_union_dedoublonne_sur_plusieurs_sous_questions(self, mock_query):
        """Les résultats de chaque sous-question sont fusionnés sans doublon."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["sous-question A", "sous-question B"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_query.side_effect = [[1, 2, 3], [3, 4, 5]]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question originale multi-sujets",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [1, 2, 3, 4, 5]

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_mono_sujet_une_seule_recherche(self, mock_query):
        """Une seule sous-question déclenche une seule recherche pgvector."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["question mono-sujet"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.5, 0.6]]
        mock_query.return_value = [10, 20, 30]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question mono-sujet",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [10, 20, 30]
        assert mock_query.call_count == 1
        embedding_client.embed_batch.assert_called_once_with(["question mono-sujet"])
