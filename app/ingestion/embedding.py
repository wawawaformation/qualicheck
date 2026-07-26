"""
Client pour le calcul d'embeddings via Azure text-embedding-3-small.

Utilise le client openai brut (pas langchain) : la réponse de l'API
expose le nombre de tokens consommés (response.usage.total_tokens),
nécessaire au suivi de coût — l'interface Embeddings de langchain
(embed_documents()) ne les expose pas.
"""

import os

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .llm_client import load_manifest

EMBEDDING_DIMENSIONS = 1536


class EmbeddingClient:
    """Client pour le calcul d'embeddings de règles (une règle = un chunk)."""

    def __init__(self):
        """Initialise le client Azure OpenAI (embeddings)."""
        manifest = load_manifest()
        role = manifest["embedding"]
        self.model_name = role["modele"]
        self.deployment_name = os.getenv(role["env_var"])

        self.client = OpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            max_retries=0,
        )
        self.total_tokens = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Calcule les embeddings d'un lot de textes (jusqu'à 50).

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        autre), avec backoff exponentiel (2s, 4s, 8s).

        Args:
            texts: Chunks à vectoriser (un par règle), un lot à la fois

        Returns:
            Vecteurs à 1536 dimensions, dans le même ordre que texts
        """
        response = self.client.embeddings.create(
            model=self.deployment_name,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        self.total_tokens += response.usage.total_tokens
        return [item.embedding for item in response.data]
