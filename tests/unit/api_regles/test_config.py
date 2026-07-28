"""Le manifeste est la seule source de vérité de la configuration de l'API."""

import pytest

from app.api_regles import config


def test_le_manifeste_expose_le_port():
    assert config.PORT == 8880


def test_le_manifeste_expose_la_longueur_max_de_note():
    assert config.REVIEW_NOTE_MAX_LENGTH == 2000


def test_le_manifeste_expose_les_origines_cors():
    assert "http://localhost:5173" in config.CORS_ALLOWED_ORIGINS
    assert "*" not in config.CORS_ALLOWED_ORIGINS


def test_le_manifeste_expose_titre_description_version():
    assert config.TITLE
    assert config.DESCRIPTION
    assert config.VERSION


def test_le_manifeste_expose_lattribution_de_licence():
    """Obligation CC BY-SA : crédit et lien vers la licence."""
    assert config.LICENCE_NOM == "CC BY-SA 4.0"
    assert config.LICENCE_URL.startswith("https://creativecommons.org/licenses/by-sa/4.0")
    assert "Opquast" in config.ATTRIBUTION


def test_admin_token_renvoie_le_secret(monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", "jeton-de-test")
    assert config.admin_token() == "jeton-de-test"


def test_admin_token_refuse_un_secret_vide(monkeypatch):
    """Sans ce garde-fou, la clé attendue serait vide et le PATCH ouvert."""
    monkeypatch.setenv("FASTAPI_API_KEY", "")
    with pytest.raises(RuntimeError, match="FASTAPI_API_KEY"):
        config.admin_token()
