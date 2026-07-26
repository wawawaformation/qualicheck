"""
Tests unitaires pour app/ingestion/embedding.py

Teste le client d'embedding Azure — aucune requête réseau réelle, le
client openai est entièrement mocké.
"""
from unittest.mock import MagicMock, patch

from app.ingestion.embedding import EmbeddingClient


def _mock_embeddings_response(vectors, total_tokens):
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    response.usage.total_tokens = total_tokens
    return response


class TestEmbeddingClient:
    """Tests du client d'embedding."""

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_returns_vectors_in_order(self, mock_openai_class):
        """embed_batch retourne les vecteurs dans le même ordre que les textes."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.return_value = _mock_embeddings_response(
            vectors=[[0.1, 0.2], [0.3, 0.4]], total_tokens=42
        )

        client = EmbeddingClient()
        vectors = client.embed_batch(["texte un", "texte deux"])

        assert vectors == [[0.1, 0.2], [0.3, 0.4]]
        assert client.total_tokens == 42

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_passes_dimensions_1536_explicitly(self, mock_openai_class):
        """L'appel API demande explicitement dimensions=1536, jamais 384."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.return_value = _mock_embeddings_response(
            vectors=[[0.1] * 1536], total_tokens=10
        )

        client = EmbeddingClient()
        client.embed_batch(["texte"])

        call_kwargs = mock_client_instance.embeddings.create.call_args.kwargs
        assert call_kwargs["dimensions"] == 1536

    @patch("app.ingestion.embedding.OpenAI")
    def test_embed_batch_accumulates_tokens_across_calls(self, mock_openai_class):
        """total_tokens s'accumule sur plusieurs appels (plusieurs lots)."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.embeddings.create.side_effect = [
            _mock_embeddings_response(vectors=[[0.1]], total_tokens=10),
            _mock_embeddings_response(vectors=[[0.2]], total_tokens=15),
        ]

        client = EmbeddingClient()
        client.embed_batch(["texte un"])
        client.embed_batch(["texte deux"])

        assert client.total_tokens == 25
