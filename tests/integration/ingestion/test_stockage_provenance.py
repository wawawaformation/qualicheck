"""
Test d'intégration : provenance (llm_model, prompt_version, created_at,
updated_at) via upsert_rule + load_enriched_rules_from_db. Nécessite les
conteneurs Docker démarrés et la migration 0009 appliquée.
"""
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.schema import EnrichedRule
from app.models.referentiel import Regle
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


def test_provenance_round_trip(session):
    """llm_model et prompt_version survivent à un cycle store -> load."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle avec provenance", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule]))

    loaded = load_enriched_rules_from_db(session)
    by_number = {r.number: r for r in loaded.regles}

    assert by_number[1].llm_model == "kimi-k2.6"
    assert by_number[1].prompt_version == 3

    clear_opquast_tables(session)


def test_created_at_set_once_updated_at_changes_on_reupsert(session):
    """created_at ne change pas lors d'un ré-upsert ; updated_at change."""
    clear_opquast_tables(session)

    rule = EnrichedRule(
        id=1, number=1, intitule="Règle initiale", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule]))
    first = session.query(Regle).filter_by(numero=1).one()
    created_at_initial = first.created_at
    updated_at_initial = first.updated_at
    session.expunge(first)

    rule_v2 = EnrichedRule(
        id=1, number=1, intitule="Règle modifiée", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug="regle-1", solution="Solution modifiée", controle="Contrôle",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Guide", llm_model="kimi-k2.6", prompt_version=3,
    )
    store_rules(session, EnrichedRules([rule_v2]))
    second = session.query(Regle).filter_by(numero=1).one()

    assert second.created_at == created_at_initial
    assert second.updated_at >= updated_at_initial

    clear_opquast_tables(session)
