"""
Ingestion de test — peuple la BDD avec les 245 règles Opquast + bouchons LLM.

Réutilise les étapes 1-3 (acquisition réelle + agrégation) mais remplace
l'enrichissement LLM par des données de test, pour valider le schéma sans
coûts tokens.

Usage: make up && make migration && uv run python scripts/ingestion_test.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.logging_config import setup_logging
from app.ingestion.acquisition import acquire_rules
from app.ingestion.aggregation import aggregate_rules
from app.ingestion.stockage import store_rules, clear_opquast_tables
from app.ingestion.schema import EnrichedRule

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")


def build_database_url():
    """Construit l'URL de connexion PostgreSQL depuis les vars d'env."""
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")

    if not all([user, password, host, db]):
        raise ValueError("PostgreSQL config incomplete in .env")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def create_enriched_rule_stub(aggregated_rule):
    """
    Crée une EnrichedRule à partir d'une RuleAggregation en remplissant
    les champs d'enrichissement par des bouchons (pas d'appel LLM).
    """
    return EnrichedRule(
        id=aggregated_rule.id,
        number=aggregated_rule.number,
        intitule=aggregated_rule.intitule,
        theme=aggregated_rule.theme,
        solution=aggregated_rule.solution,
        controle=aggregated_rule.controle,
        objectifs=aggregated_rule.objectifs,
        tags=aggregated_rule.tags,
        phases=aggregated_rule.phases,
        slug=aggregated_rule.slug,
        strategie_analyse="test",
        strategie_justification="Test justification — enrichissement bypassed pour validation schéma",
        guide_analyse="Test guide — voir scripts/ingestion_test.py pour détails",
        strategie_source="ia_import",
        llm_provider="test",
    )


def main():
    """Exécute l'ingestion de test (étapes 1-2 réelles + 3 avec bouchons)."""
    setup_logging()

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

    try:
        # Étape 1 — Acquisition réelle (API + scraping Opquast)
        logger.info("Étape 1 — Acquisition : démarrage")
        acquired_rules = acquire_rules()
        progress_logger.info(f"Étape 1 — Acquisition : {len(acquired_rules)} règles acquises")

        # Étape 2 — Agrégation réelle (validation Pydantic)
        logger.info("Étape 2 — Agrégation : démarrage")
        aggregated = aggregate_rules(acquired_rules)
        progress_logger.info(f"Étape 2 — Agrégation : {len(aggregated.regles)} règles validées")

        # Étape 3 — Enrichissement avec bouchons (pas de LLM)
        logger.info("Étape 3 — Enrichissement (BOUCHONS) : démarrage")
        enriched_list = []
        for rule in aggregated.regles:
            enriched = create_enriched_rule_stub(rule)
            enriched_list.append(enriched)
            progress_logger.info(f"Règle {rule.number} — enrichissement (bouchon) : OK")

        logger.info(f"Étape 3 — Enrichissement : {len(enriched_list)} règles enrichies (bouchons)")

        # Étape 4 — Stockage en BDD
        logger.info("Étape 4 — Stockage : démarrage")
        database_url = build_database_url()
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Vide les tables Opquast avant d'insérer
            clear_opquast_tables(session)

            # Insère les 245 règles dans une transaction unique
            from app.ingestion.aggregation import EnrichedRules
            enriched_rules = EnrichedRules(enriched_list)
            store_rules(session, enriched_rules)

            progress_logger.info(f"Étape 4 — Stockage : {len(enriched_list)} règles stockées")
            logger.info("✓ Ingestion complète réussie")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"✗ Erreur ingestion : {e}")
        raise


if __name__ == "__main__":
    main()
