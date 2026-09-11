"""
Orchestration du retrieval : décomposition, embedding, recherche pgvector,
union. Voir docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md
et docs/superpowers/specs/2026-09-11-retrieval-refus-design.md.
"""

from sqlalchemy.orm import Session

from app.ingestion.embedding import EmbeddingClient
from app.ingestion.rag_acceptance import query_top_n_numeros
from app.retrieval.decomposition import DecompositionClient


def retrieve(
    session: Session,
    question: str,
    top_n: int,
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> list[tuple[int, float]]:
    """Retrouve les (numéro, score) de règle pertinents pour une question.

    Décompose la question en 1..N sous-questions, vectorise toutes les
    sous-questions en un seul appel embed_batch, interroge pgvector
    (top_n) une fois par sous-question, puis fusionne par union simple
    dédoublonnée (ordre de première apparition). En cas de doublon entre
    sous-questions, le score gardé est le meilleur (le plus similaire),
    pas celui de la première apparition. Pas de plafond après fusion : la
    taille du résultat varie selon le nombre de sous-questions.
    """
    sous_questions = decomposition_client.decomposer(question)
    vectors = embedding_client.embed_batch(sous_questions)

    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for vector in vectors:
        for numero, score in query_top_n_numeros(session, vector, top_n):
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score

    return [(numero, meilleurs_scores[numero]) for numero in ordre]
