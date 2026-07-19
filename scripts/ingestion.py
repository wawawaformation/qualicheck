"""Point d'entrée pour le pipeline d'ingestion complet.

Orchestre les étapes du pipeline en séquence (acquisition → agrégation →
enrichissement → stockage), applique le principe fail-fast : toute erreur
sur une étape arrête immédiatement le script avec un code de sortie non-nul.

Étapes 5-7 (chunking, embedding, indexation) pas encore implémentées —
seront ajoutées à ce même script dans une session future.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.acquisition import acquire_rules  # noqa: E402
from app.ingestion.aggregation import aggregate_rules  # noqa: E402
from app.ingestion.enrichment import enrich_rules  # noqa: E402
from app.ingestion.stockage import clear_opquast_tables, count_rules, store_rules  # noqa: E402
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


def parse_args() -> argparse.Namespace:
    """Parse les arguments CLI du script."""
    parser = argparse.ArgumentParser(description="Pipeline d'ingestion QualiCheck")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ne traite que les N premières règles (défaut : toutes)",
    )
    return parser.parse_args()


def check_existing_data(session: Session) -> None:
    """
    Si des règles existent déjà, demande à l'utilisateur s'il s'agit d'une
    nouvelle ingestion (vide les tables Opquast puis continue) ou d'une
    mise à jour (non implémentée en MVP, arrête le script).

    Args:
        session: Session SQLAlchemy active
    """
    existing_count = count_rules(session)
    if existing_count == 0:
        return

    progress_logger.info(
        f"{existing_count} règle(s) déjà présente(s) en base."
    )
    choice = input("Nouvelle ingestion [n] ou mise à jour [m] ? ").strip().lower()

    if choice == "m":
        progress_logger.info("Mise à jour : pas encore implémentée (hors MVP).")
        sys.exit(0)

    if choice != "n":
        progress_logger.info("Choix non reconnu, arrêt du script.")
        sys.exit(0)

    confirm = input(
        f"Cela va supprimer les {existing_count} règle(s) existante(s). Confirmer ? [y/N] "
    ).strip().lower()
    if confirm != "y":
        progress_logger.info("Suppression annulée, arrêt du script.")
        sys.exit(0)

    clear_opquast_tables(session)


def main() -> None:
    args = parse_args()
    setup_logging()
    load_dotenv()

    engine = get_engine()
    with Session(engine) as session:
        check_existing_data(session)

    logger.info("=== Pipeline d'ingestion : démarrage ===")
    progress_logger.info("=== Pipeline d'ingestion : démarrage ===")

    try:
        logger.info("Étape 1 — Acquisition : démarrage")
        progress_logger.info("Étape 1 — Acquisition : démarrage")
        acquired = acquire_rules(limit=args.limit)
        logger.info("Étape 1 — Acquisition : terminée (%d règles)", len(acquired))
    except Exception as e:
        logger.error("Étape 1 — Acquisition : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 2 — Agrégation : démarrage")
        progress_logger.info("Étape 2 — Agrégation : démarrage")
        rules = aggregate_rules(acquired)
        logger.info("Étape 2 — Agrégation : terminée")
    except Exception as e:
        logger.error("Étape 2 — Agrégation : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 3 — Enrichissement : démarrage")
        progress_logger.info("Étape 3 — Enrichissement : démarrage")
        enriched = enrich_rules(rules)
        logger.info("Étape 3 — Enrichissement : terminée")
    except Exception as e:
        logger.error("Étape 3 — Enrichissement : ÉCHEC (%s)", e)
        sys.exit(1)

    try:
        logger.info("Étape 4 — Stockage : démarrage")
        progress_logger.info("Étape 4 — Stockage : démarrage")
        with Session(engine) as session:
            store_rules(session, enriched)
        logger.info("Étape 4 — Stockage : terminée")
    except Exception as e:
        logger.error("Étape 4 — Stockage : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== Pipeline d'ingestion : succès (Étapes 1-4) ===")
    progress_logger.info("=== Pipeline d'ingestion : succès (Étapes 1-4) ===")


if __name__ == "__main__":
    main()
