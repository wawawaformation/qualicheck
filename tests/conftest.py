"""
Configuration pytest partagée — fixtures, mocks, setup.

Chargée automatiquement par pytest avant tous les tests.
"""

import pytest


@pytest.fixture(autouse=True)
def setup_env_variables(monkeypatch):
    """
    Configure les variables d'environnement pour les tests.

    autouse=True : la fixture s'applique à tous les tests automatiquement.
    monkeypatch : fixture pytest intégrée pour modifier temporairement les variables.
    """
    monkeypatch.setenv("OPQUAST_SITE_BASE_URL", "https://checklists.opquast.com/fr/qualite-numerique/")
    monkeypatch.setenv("OPQUAST_API_BASE_URL", "https://api.opquast.com/checklist/public/")
