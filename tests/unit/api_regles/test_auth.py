"""Garde d'écriture : token Bearer statique, 401 dans tous les cas d'échec."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api_regles.auth import require_bearer

JETON = "jeton-de-test"


def _identifiants(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_token_valide_passe(monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", JETON)

    assert require_bearer(_identifiants(JETON)) is None


def test_token_faux_leve_401(monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", JETON)

    with pytest.raises(HTTPException) as erreur:
        require_bearer(_identifiants("mauvais-jeton"))

    assert erreur.value.status_code == 401


def test_header_absent_leve_401_et_non_403(monkeypatch):
    """401 = aucune identité fournie. HTTPBearer renverrait 403 par défaut."""
    monkeypatch.setenv("FASTAPI_API_KEY", JETON)

    with pytest.raises(HTTPException) as erreur:
        require_bearer(None)

    assert erreur.value.status_code == 401


def test_secret_absent_empeche_toute_ecriture(monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", "")

    with pytest.raises(RuntimeError, match="FASTAPI_API_KEY"):
        require_bearer(_identifiants(JETON))
