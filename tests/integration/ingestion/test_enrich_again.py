"""
Test d'intégration : sélection des règles à revoir et nettoyage des champs
de revue (enrich_again). Nécessite qualicheck-postgres démarré et
POSTGRES_TEST_DB migrée (make migration-test).
"""
import os
from datetime import UTC, datetime

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.enrich_again import clear_review_fields, load_rules_to_review
from app.ingestion.schema import EnrichedRule
from app.ingestion.stockage import clear_opquast_tables, store_rules
from app.models.referentiel import Regle

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


def _rule(number, strategie_analyse):
    return EnrichedRule(
        id=number, number=number, intitule=f"Règle {number}", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug=f"regle-{number}", solution="Solution", controle="Contrôle",
        strategie_analyse=strategie_analyse, strategie_justification="Justif",
        guide_analyse="Guide",
    )


def test_load_rules_to_review_filters_by_status(session):
    """Seules les règles a_revoir/invalide sont retournées, pas valide ni NULL."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([
        _rule(1, "statique"),
        _rule(2, "playwright"),
        _rule(3, "manuel"),
    ]))

    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Note 1"}
    )
    session.query(Regle).filter_by(numero=2).update(
        {"review_status": "valide", "review_note": "Note 2"}
    )
    # numero=3 reste NULL (jamais revue)
    session.commit()

    to_review = load_rules_to_review(session)

    numeros = {rule.number for rule, _, _ in to_review}
    assert numeros == {1}

    rule, note, current = next(t for t in to_review if t[0].number == 1)
    assert note == "Note 1"
    assert current == "statique"

    clear_opquast_tables(session)


def test_load_rules_to_review_includes_invalide_status(session):
    """review_status='invalide' est aussi sélectionné, pas seulement a_revoir."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "invalide", "review_note": "Note"}
    )
    session.commit()

    to_review = load_rules_to_review(session)

    assert {rule.number for rule, _, _ in to_review} == {1}

    clear_opquast_tables(session)


def test_clear_review_fields_resets_to_null(session):
    """clear_review_fields remet reviewed_at/review_status/review_note à NULL."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    session.query(Regle).filter_by(numero=1).update({
        "review_status": "a_revoir",
        "review_note": "Note",
        "reviewed_at": datetime.now(UTC).replace(tzinfo=None),
    })
    session.commit()

    clear_review_fields(session, numero=1)
    session.commit()

    regle = session.query(Regle).filter_by(numero=1).first()
    assert regle.review_status is None
    assert regle.review_note is None
    assert regle.reviewed_at is None

    clear_opquast_tables(session)
