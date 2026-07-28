"""
Tests d'intégration de l'API données.

Nécessite qualicheck-postgres démarré et POSTGRES_TEST_DB migrée
(make migration-test).

La session de test est injectée par app.dependency_overrides : l'API sous test
ne peut alors PHYSIQUEMENT PAS ouvrir de connexion vers POSTGRES_DB. Garantie
structurelle, pas affaire de variable d'environnement bien positionnée —
précaution issue de l'incident du 2026-07-25.
"""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api_regles.main import app
from app.db import get_session
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
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def jeu_de_regles(session):
    """4 règles : statique, playwright, composite, et une marquée a_revoir."""
    clear_opquast_tables(session)

    theme = Theme(theme="Contenus")
    session.add(theme)
    session.flush()

    session.add_all(
        [
            Regle(
                theme_id=theme.id,
                numero=1,
                intitule="Règle statique",
                solution="Solution 1",
                controle="Contrôle 1",
                strategie_analyse="statique",
                strategie_source="ia_import",
                guide_analyse="Guide 1",
            ),
            Regle(
                theme_id=theme.id,
                numero=2,
                intitule="Règle playwright",
                solution="Solution 2",
                controle="Contrôle 2",
                strategie_analyse="playwright",
                strategie_source="ia_import",
                guide_analyse="Guide 2",
            ),
            Regle(
                theme_id=theme.id,
                numero=3,
                intitule="Règle composite",
                solution="Solution 3",
                controle="Contrôle 3",
                strategie_analyse="statique&playwright",
                strategie_source="ia_reingest",
                guide_analyse="Guide 3",
            ),
            Regle(
                theme_id=theme.id,
                numero=4,
                intitule="Règle marquée",
                solution="Solution 4",
                controle="Contrôle 4",
                strategie_analyse="manuel",
                strategie_source="ia_import",
                guide_analyse="Guide 4",
                review_status="a_revoir",
                review_note="À reclasser",
            ),
        ]
    )
    session.commit()


def test_health_repond_ok_quand_la_base_repond(client):
    reponse = client.get("/health")

    assert reponse.status_code == 200
    assert reponse.json()["status"] == "ok"
    assert reponse.json()["base"] == "ok"
    assert reponse.json()["version"]


def test_health_repond_503_quand_la_base_est_injoignable(session):
    """Une sonde qui ne vérifie pas la base déclarerait l'API saine à tort."""

    class SessionEnEchec:
        def execute(self, *args, **kwargs):
            raise RuntimeError("base injoignable")

    app.dependency_overrides[get_session] = lambda: SessionEnEchec()
    try:
        reponse = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()

    assert reponse.status_code == 503
    assert reponse.json()["base"] == "injoignable"


def test_la_documentation_openapi_est_servie(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_la_documentation_porte_lattribution_cc_by_sa(client):
    """Obligation de la licence du référentiel, pas une mention de courtoisie."""
    schema = client.get("/openapi.json").json()

    assert schema["info"]["license"]["name"] == "CC BY-SA 4.0"
    assert "creativecommons.org/licenses/by-sa/4.0" in schema["info"]["license"]["url"]
    assert "Opquast" in schema["info"]["description"]
