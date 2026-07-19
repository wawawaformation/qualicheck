"""Vide les tables du référentiel Opquast (theme, regle, objectif, phase, tag
et leurs tables d'association), sans toucher au cœur métier QualiCheck
(utilisateur, audit, page, constat).

Utile pour retester une ingestion sans redescendre/remonter toute la
migration Alembic.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)

TABLES_OPQUAST = [
    "regle_tag",
    "phase_regle",
    "objectif_regle",
    "regle",
    "theme",
    "objectif",
    "phase",
    "tag",
]


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
    tables = ", ".join(TABLES_OPQUAST)

    logger.info("Vidage des tables Opquast : %s", tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    logger.info("Tables Opquast vidées avec succès")


if __name__ == "__main__":
    main()
