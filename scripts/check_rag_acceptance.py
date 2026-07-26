"""Point d'entrée pour rejouer le jeu d'acceptance RAG (retrieval sémantique).

Recalcule l'embedding réel de chaque question du jeu de cas
(tests/acceptance/rag_acceptance.jsonl), interroge pgvector (similarité
cosinus) et vérifie que la règle attendue figure dans le top_n déclaré
dans app/ingestion/manifest.yml (section rag_acceptance). Coût réel à
chaque exécution (appel Azure embeddings), volontairement hors CI —
lancé à la demande via `make rag-acceptance`.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_reussite,
    evaluate_case,
    format_dataset_versions,
    is_acceptable,
    load_cases,
    query_top_n_numeros,
    summarize_dataset_versions,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    config = load_manifest()["rag_acceptance"]
    top_n = config["top_n"]
    seuil = config["taux_reussite_minimum"]

    logger.info("=== check_rag_acceptance : démarrage ===")
    progress_logger.info("=== check_rag_acceptance : démarrage ===")

    try:
        cases = load_cases(CASES_PATH)
        client = EmbeddingClient()
        vectors = client.embed_batch([case["question"] for case in cases])

        evaluations = []
        with Session(engine) as session:
            dataset_summary = format_dataset_versions(summarize_dataset_versions(session))
            progress_logger.info(f"check_rag_acceptance — Jeu de données : {dataset_summary}")

            for case, vector in zip(cases, vectors, strict=True):
                numeros_retournes = query_top_n_numeros(session, vector, top_n)
                evaluation = evaluate_case(case, numeros_retournes)
                evaluations.append(evaluation)
                statut = "OK" if evaluation["reussi"] else "ÉCHEC"
                progress_logger.info(
                    f"check_rag_acceptance — « {case['question']} » "
                    f"(règle {case['numero_regle_attendue']} attendue, "
                    f"retournées {numeros_retournes}) — {statut}"
                )

        taux = compute_taux_reussite(evaluations)
        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = (
            f"check_rag_acceptance — Taux de réussite : {taux:.0%} "
            f"(seuil {seuil:.0%}), tokens : {client.total_tokens}, "
            f"coût estimé : {cost:.4f} €"
        )
        logger.info(summary)
        progress_logger.info(summary)

    except Exception as e:
        logger.error("check_rag_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    if not is_acceptable(taux, seuil):
        logger.error("check_rag_acceptance : taux de réussite sous le seuil minimum")
        sys.exit(1)

    logger.info("=== check_rag_acceptance : succès ===")
    progress_logger.info("=== check_rag_acceptance : succès ===")


if __name__ == "__main__":
    main()
