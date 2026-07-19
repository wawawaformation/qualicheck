"""
Test d'intégration : round-trip du champ contexte via upsert_rule +
load_enriched_rules_from_db. Nécessite les conteneurs Docker démarrés
et la migration 0006 appliquée.
"""
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.schema import EnrichedRule
from app.ingestion.stockage import clear_opquast_tables, load_enriched_rules_from_db, store_rules

load_dotenv()


def _database_url():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_contexte_round_trip(session):
    """Vérifie que contexte survit à un cycle store -> load, y compris None."""
    clear_opquast_tables(session)

    rule_with_contexte = EnrichedRule(
        id=1, number=1, intitule="Règle avec contexte", theme="Thème",
        contexte="Texte explicatif de test",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    rule_without_contexte = EnrichedRule(
        id=2, number=2, intitule="Règle sans contexte", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-2", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    store_rules(session, EnrichedRules([rule_with_contexte, rule_without_contexte]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].contexte == "Texte explicatif de test"
    assert by_number[2].contexte is None

    clear_opquast_tables(session)
