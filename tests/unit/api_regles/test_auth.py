"""Garde d'écriture : un jeton Bearer par client, 401 dans tous les cas d'échec."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api_regles import config
from app.api_regles.auth import require_bearer

JETON = "jeton-de-test"


def _identifiants(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_token_valide_renvoie_le_nom_du_client(monkeypatch):
    monkeypatch.setenv("FASTAPI_API_KEY", JETON)

    assert require_bearer(_identifiants(JETON)) == "dev"


def test_plusieurs_clients_sont_distingues(monkeypatch):
    """Le nom résolu dépend du jeton reçu, pas seulement de sa validité."""
    monkeypatch.setattr(
        config,
        "CLIENTS",
        [
            {"nom": "dev", "env_var_token": "FASTAPI_API_KEY"},
            {"nom": "elie-sloim", "env_var_token": "FASTAPI_API_KEY_ELIE"},
        ],
    )
    monkeypatch.setenv("FASTAPI_API_KEY", "jeton-dev")
    monkeypatch.setenv("FASTAPI_API_KEY_ELIE", "jeton-elie")

    assert require_bearer(_identifiants("jeton-dev")) == "dev"
    assert require_bearer(_identifiants("jeton-elie")) == "elie-sloim"


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
