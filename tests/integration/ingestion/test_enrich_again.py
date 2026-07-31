"""
Test d'intégration : sélection des règles à revoir et nettoyage des champs
de revue (enrich_again). Nécessite qualicheck-postgres démarré et
POSTGRES_TEST_DB migrée (make migration-test).
"""
import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

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
    """Seules les règles a_revoir sont retournées, pas valide ni NULL."""
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


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_no_rules_to_review_skips_llm_call(mock_llm_client_class, session):
    """Aucune règle a_revoir -> aucun appel LLM, aucune erreur."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    # Aucune règle marquée pour revue

    enrich_again(session)

    mock_llm_client_class.assert_not_called()

    clear_opquast_tables(session)


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_dry_run_writes_preview_without_llm_call(mock_llm_client_class, session):
    """dry_run=True écrit l'aperçu JSON mais n'instancie jamais LLMClient."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([_rule(1, "vision+statique")]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Note"}
    )
    session.commit()

    enrich_again(session, dry_run=True)

    mock_llm_client_class.assert_not_called()

    regle = session.query(Regle).filter_by(numero=1).first()
    assert regle.review_status == "a_revoir"  # inchangé, aucun traitement effectué

    clear_opquast_tables(session)


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_success_clears_review_and_writes_ia_reingest(
    mock_llm_client_class, session
):
    """Une règle corrigée avec succès : strategie_source='ia_reingest',
    review_* remis à NULL."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([_rule(1, "vision+statique")]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Devrait être vision&statique."}
    )
    session.commit()

    mock_llm_instance = MagicMock()
    mock_llm_client_class.return_value = mock_llm_instance
    mock_llm_instance.input_tokens = 100
    mock_llm_instance.output_tokens = 50
    mock_llm_instance.enrich_single_rule.return_value = _rule(
        1, "vision&statique"
    ).model_copy(update={"strategie_source": "ia_reingest"})

    enrich_again(session)

    mock_llm_instance.enrich_single_rule.assert_called_once()
    call_args = mock_llm_instance.enrich_single_rule.call_args
    assert call_args.args[0].number == 1
    assert call_args.kwargs["review_note"] == "Devrait être vision&statique."
    assert call_args.kwargs["current_strategie_analyse"] == "vision+statique"
    assert call_args.kwargs["strategie_source"] == "ia_reingest"

    regle = session.query(Regle).filter_by(numero=1).first()
    assert regle.strategie_analyse == "vision&statique"
    assert regle.strategie_source == "ia_reingest"
    assert regle.review_status is None
    assert regle.review_note is None
    assert regle.reviewed_at is None

    clear_opquast_tables(session)


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_partial_failure_preserves_prior_successes(
    mock_llm_client_class, session
):
    """Si la 2e règle échoue après ses tentatives, la 1ère (déjà corrigée et
    commitée) reste acquise ; la 2e garde son review_status intact."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([
        _rule(1, "vision+statique"),
        _rule(2, "statique"),
    ]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Note 1"}
    )
    session.query(Regle).filter_by(numero=2).update(
        {"review_status": "a_revoir", "review_note": "Note 2"}
    )
    session.commit()

    mock_llm_instance = MagicMock()
    mock_llm_client_class.return_value = mock_llm_instance
    mock_llm_instance.input_tokens = 100
    mock_llm_instance.output_tokens = 50
    fixed_rule_1 = _rule(1, "vision&statique").model_copy(
        update={"strategie_source": "ia_reingest"}
    )
    mock_llm_instance.enrich_single_rule.side_effect = [
        fixed_rule_1,
        TimeoutError("3 tentatives épuisées"),
    ]

    with pytest.raises(TimeoutError):
        enrich_again(session)

    r1 = session.query(Regle).filter_by(numero=1).first()
    assert r1.strategie_analyse == "vision&statique"
    assert r1.review_status is None  # traitée avec succès, nettoyée et acquise

    r2 = session.query(Regle).filter_by(numero=2).first()
    assert r2.review_status == "a_revoir"  # échec, conservée intacte
    assert r2.review_note == "Note 2"

    clear_opquast_tables(session)
