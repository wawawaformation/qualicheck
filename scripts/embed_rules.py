"""Point d'entrée pour le calcul d'embedding de toutes les règles.

Recalcule l'embedding des 245 règles à chaque exécution (pas seulement
celles à NULL) — plus simple, coût négligeable sur ce volume. Fail-fast :
toute erreur arrête immédiatement le script avec un code de sortie
non-nul.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunking import build_chunk_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.stockage import load_enriched_rules_from_db, upsert_rule  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

BATCH_SIZE = 50


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

    logger.info("=== embed_rules : démarrage ===")
    progress_logger.info("=== embed_rules : démarrage ===")

    try:
        with Session(engine) as session:
            enriched_rules = load_enriched_rules_from_db(session)

        rules = enriched_rules.regles
        progress_logger.info(f"embed_rules : {len(rules)} règle(s) à vectoriser")

        client = EmbeddingClient()

        for i in range(0, len(rules), BATCH_SIZE):
            batch = rules[i : i + BATCH_SIZE]
            texts = [build_chunk_text(rule) for rule in batch]
            vectors = client.embed_batch(texts)
            for rule, vector in zip(batch, vectors, strict=True):
                rule.embedding = vector
            progress_logger.info(
                f"embed_rules : lot {i // BATCH_SIZE + 1} ({len(batch)} règles) — OK"
            )

        with Session(engine) as session:
            for rule in rules:
                upsert_rule(session, rule)
            session.commit()

        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = f"embed_rules — Tokens : {client.total_tokens}, coût estimé : {cost:.4f} €"
        logger.info(summary)
        progress_logger.info(summary)

    except Exception as e:
        logger.error("embed_rules : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== embed_rules : succès ===")
    progress_logger.info("=== embed_rules : succès ===")


if __name__ == "__main__":
    main()
