"""
Tests d'intégration de POST /regles/dense.

retrieve() est mocké : jamais d'appel LLM réel dans ces tests. Nécessite
qualicheck-postgres démarré et POSTGRES_TEST_DB migrée (make migration-test).
"""

import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api_regles.main import app
from app.db import get_session_referentiel
from app.ingestion.stockage import clear_opquast_tables
from app.models.referentiel import Regle, Theme

load_dotenv()

JETON = "jeton-de-test"


def _database_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", JETON)
    monkeypatch.setenv("FASTAPI_API_KEY_ELIE", "jeton-elie-test")
    monkeypatch.setenv("FASTAPI_API_KEY_DAVID", "jeton-david-test")
    monkeypatch.setenv("FASTAPI_API_KEY_FORMATEUR", "jeton-formateur-test")
    app.dependency_overrides[get_session_referentiel] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def jeu_de_regles(session):
    """2 règles, suffisant pour vérifier l'ordre de la réponse."""
    clear_opquast_tables(session)

    theme = Theme(theme="Contenus")
    session.add(theme)
    session.flush()

    session.add_all(
        [
            Regle(
                theme_id=theme.id,
                numero=1,
                intitule="Règle un",
                solution="Solution 1",
                controle="Contrôle 1",
                strategie_analyse="statique",
                strategie_source="ia_import",
                guide_analyse="Guide 1",
            ),
            Regle(
                theme_id=theme.id,
                numero=3,
                intitule="Règle trois",
                solution="Solution 3",
                controle="Contrôle 3",
                strategie_analyse="statique",
                strategie_source="ia_import",
                guide_analyse="Guide 3",
            ),
        ]
    )
    session.commit()


def _entetes(token: str = JETON) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@patch("app.api_regles.regles.retrieve")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_retrieve, client, jeu_de_regles
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro."""
    mock_retrieve.return_value = [3, 1]

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 200
    numeros = [r["numero"] for r in reponse.json()]
    assert numeros == [3, 1]


@patch("app.api_regles.regles.retrieve")
def test_dense_sans_jeton_donne_401(mock_retrieve, client, jeu_de_regles):
    reponse = client.post("/regles/dense", json={"question": "Question de test"})

    assert reponse.status_code == 401
    mock_retrieve.assert_not_called()


@patch("app.api_regles.regles.retrieve")
def test_dense_question_vide_donne_422(mock_retrieve, client, jeu_de_regles):
    reponse = client.post("/regles/dense", json={"question": ""}, headers=_entetes())

    assert reponse.status_code == 422
    mock_retrieve.assert_not_called()


@patch("app.api_regles.regles.retrieve")
def test_dense_echec_retrieve_donne_503(mock_retrieve, client, jeu_de_regles):
    mock_retrieve.side_effect = RuntimeError("embedding indisponible")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 503


@patch("app.api_regles.regles.retrieve")
def test_dense_journalise_la_question_et_le_client(
    mock_retrieve, client, jeu_de_regles, caplog
):
    mock_retrieve.return_value = [1]

    with caplog.at_level("INFO", logger="app.api_regles.regles"):
        client.post(
            "/regles/dense",
            json={"question": "Question de test"},
            headers=_entetes(),
        )

    assert "dev" in caplog.text
    assert "Question de test" in caplog.text
