"""
Test d'intégration : embedding survit à un cycle store -> load.
Nécessite qualicheck-postgres démarré et POSTGRES_TEST_DB migrée
(make migration-test, migration 0011 incluse — vector(1536)).
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
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_embedding_round_trip(session):
    """Un embedding de 1536 flottants survit à un cycle store -> load."""
    clear_opquast_tables(session)

    vecteur = [0.001 * i for i in range(1536)]
    rule = EnrichedRule(
        id=1, number=1, intitule="Règle avec embedding", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", embedding=vecteur,
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].embedding is not None
    assert len(by_number[1].embedding) == 1536
    assert by_number[1].embedding[0] == pytest.approx(0.0)
    assert by_number[1].embedding[1] == pytest.approx(0.001)

    clear_opquast_tables(session)


def test_embedding_stays_null_when_not_provided(session):
    """Une règle sans embedding fourni reste NULL en base (pas de valeur par défaut)."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle sans embedding", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide",
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].embedding is None

    clear_opquast_tables(session)
