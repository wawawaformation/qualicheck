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


def test_liste_toutes_les_regles_triees_par_numero(client, jeu_de_regles):
    reponse = client.get("/regles")

    assert reponse.status_code == 200
    assert [regle["numero"] for regle in reponse.json()] == [1, 2, 3, 4]


def test_liste_expose_le_theme_et_les_outils_derives(client, jeu_de_regles):
    composite = next(r for r in client.get("/regles").json() if r["numero"] == 3)

    assert composite["theme"] == "Contenus"
    assert composite["strategie_analyse"] == "statique&playwright"
    assert composite["outils"] == ["statique", "playwright"]


def test_filtre_outil_inclut_les_composites(client, jeu_de_regles):
    """« contient playwright », pas « égale playwright » : la composite doit sortir."""
    numeros = [r["numero"] for r in client.get("/regles?outil=playwright").json()]

    assert numeros == [2, 3]


def test_filtre_outil_repetable_est_un_ou(client, jeu_de_regles):
    numeros = [
        r["numero"] for r in client.get("/regles?outil=manuel&outil=playwright").json()
    ]

    assert numeros == [2, 3, 4]


def test_filtre_review_status_aucun_exclut_les_regles_marquees(client, jeu_de_regles):
    numeros = [r["numero"] for r in client.get("/regles?review_status=aucun").json()]

    assert numeros == [1, 2, 3]


def test_filtre_review_status_selectionne_les_regles_marquees(client, jeu_de_regles):
    numeros = [r["numero"] for r in client.get("/regles?review_status=a_revoir").json()]

    assert numeros == [4]


def test_les_deux_criteres_se_combinent_en_et(client, jeu_de_regles):
    numeros = [
        r["numero"]
        for r in client.get("/regles?outil=playwright&review_status=aucun").json()
    ]

    assert numeros == [2, 3]


def test_valeur_de_filtre_hors_enumeration_est_refusee(client, jeu_de_regles):
    assert client.get("/regles?outil=valeurinvalide").status_code == 422


def test_lecture_dune_regle_par_son_numero(client, jeu_de_regles):
    reponse = client.get("/regles/3")

    assert reponse.status_code == 200
    assert reponse.json()["numero"] == 3
    assert reponse.json()["outils"] == ["statique", "playwright"]


def test_numero_inconnu_donne_404(client, jeu_de_regles):
    assert client.get("/regles/9999").status_code == 404


def test_numero_non_entier_donne_422(client, jeu_de_regles):
    assert client.get("/regles/abc").status_code == 422
