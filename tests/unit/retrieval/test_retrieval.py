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
        mock_query.side_effect = [
            [(1, 0.9), (2, 0.5), (3, 0.3)],
            [(3, 0.6), (4, 0.4), (5, 0.2)],
        ]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question originale multi-sujets",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(1, 0.9), (2, 0.5), (3, 0.6), (4, 0.4), (5, 0.2)]

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_garde_le_meilleur_score_en_cas_de_doublon(self, mock_query):
        """Le numéro 3 apparaît dans les deux sous-questions : le score gardé
        est le plus haut (0.6), pas le premier trouvé (0.3)."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["sous-question A", "sous-question B"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_query.side_effect = [
            [(3, 0.3)],
            [(3, 0.6)],
        ]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(3, 0.6)]

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_mono_sujet_une_seule_recherche(self, mock_query):
        """Une seule sous-question déclenche une seule recherche pgvector."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["question mono-sujet"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.5, 0.6]]
        mock_query.return_value = [(10, 0.9), (20, 0.5), (30, 0.2)]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question mono-sujet",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(10, 0.9), (20, 0.5), (30, 0.2)]
        assert mock_query.call_count == 1
        embedding_client.embed_batch.assert_called_once_with(["question mono-sujet"])
