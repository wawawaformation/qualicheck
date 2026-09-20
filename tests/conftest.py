"""
Configuration pytest partagée — fixtures, mocks, setup.

Chargée automatiquement par pytest avant tous les tests.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def tracage_inerte(tmp_path_factory):
    """
    Rend toute la suite inerte vis-à-vis du traçage OpenTelemetry réel.

    Sans ça, un test qui appelle `repondre()` ou `retrieve()` sans mocker
    `get_tracer` déclenche le vrai `setup_tracing()` : spans écrits dans le
    fichier JSONL du dépôt (y compris en CI), et TracerProvider global qui
    écrit sur disque pour le reste de la session (singleton de module).

    - `APP_ENV=test` : les traces de test ne se confondent jamais avec du
      trafic dev/staging/prod (attribut `deployment.environment.name`).
    - `OTEL_EXPORTER=jsonl` : un `.env` local en mode `otlp` ne peut pas
      faire partir la suite sur le réseau (Langfuse Cloud).
    - `OTEL_JSONL_PATH` : redirigé hors du dépôt.

    Portée `session` : la fixture doit agir avant que le moindre test
    déclenche `setup_tracing()`, qui mémorise son provider une fois pour
    toutes.
    """
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("OTEL_EXPORTER", "jsonl")
    monkeypatch.setenv(
        "OTEL_JSONL_PATH", str(tmp_path_factory.mktemp("traces") / "traces.jsonl")
    )
    yield
    monkeypatch.undo()


@pytest.fixture(autouse=True)
def setup_env_variables(monkeypatch):
    """
    Configure les variables d'environnement pour les tests.

    autouse=True : la fixture s'applique à tous les tests automatiquement.
    monkeypatch : fixture pytest intégrée pour modifier temporairement les variables.
    """
    monkeypatch.setenv("OPQUAST_SITE_BASE_URL", "https://checklists.opquast.com/fr/qualite-numerique/")
    monkeypatch.setenv("OPQUAST_API_BASE_URL", "https://api.opquast.com/checklist/public/")
