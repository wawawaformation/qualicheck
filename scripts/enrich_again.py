"""Point d'entrée pour la réécriture ciblée des règles marquées à revoir.

Rappelle le LLM d'enrichissement sur les règles review_status IN
(a_revoir, invalide), en tenant compte de review_note, puis vide ces
champs une fois la correction appliquée. Fail-fast : toute erreur arrête
immédiatement le script avec un code de sortie non-nul — les règles déjà
corrigées avant l'échec restent acquises (commit par règle).
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.enrich_again import enrich_again  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")


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

    logger.info("=== enrich_again : démarrage ===")
    progress_logger.info("=== enrich_again : démarrage ===")

    try:
        with Session(engine) as session:
            enrich_again(session)
    except Exception as e:
        logger.error("enrich_again : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== enrich_again : succès ===")
    progress_logger.info("=== enrich_again : succès ===")


if __name__ == "__main__":
    main()
