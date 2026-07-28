"""
Tests unitaires pour app/api_regles/acceptance.py

Logique pure (load_cases, is_acceptable) et evaluate_case mocké via
httpx.MockTransport — aucun appel réseau réel ni API démarrée ici. La suite
complète, contre l'API réellement démarrée, est validée par exécution
réelle via `make api-regles-acceptance`.
"""

import httpx

from app.api_regles import config
from app.api_regles.acceptance import evaluate_case, is_acceptable, load_cases


def _un_seul_client(monkeypatch):
    """Isole CLIENTS : ces tests ne doivent pas dépendre du nombre réel de
    clients déclarés dans le manifeste ni du contenu réel de .env."""
    monkeypatch.setattr(
        config, "CLIENTS", [{"nom": "dev", "env_var_token": "FASTAPI_API_KEY"}]
    )


def test_load_cases_parses_jsonl(tmp_path):
    """load_cases lit un fichier JSONL, une entrée par ligne."""
    jsonl_path = tmp_path / "cases.jsonl"
    jsonl_path.write_text(
        '{"methode": "GET", "description": "D1", "chemin": "/regles", "nombre_attendu": 245}\n'
        '{"methode": "PATCH", "description": "D2", "chemin": "/regles/1", '
        '"jeton": null, "corps": {"review_status": null}, "code_attendu": 401}\n',
        encoding="utf-8",
    )

    cases = load_cases(jsonl_path)

    assert cases == [
        {"methode": "GET", "description": "D1", "chemin": "/regles", "nombre_attendu": 245},
        {
            "methode": "PATCH",
            "description": "D2",
            "chemin": "/regles/1",
            "jeton": None,
            "corps": {"review_status": None},
            "code_attendu": 401,
        },
    ]


def _client_get_mock(nombre_regles: int) -> httpx.Client:
    """Client httpx dont le transport renvoie une liste factice de N règles."""

    def repondre(requete: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"numero": i} for i in range(nombre_regles)])

    return httpx.Client(transport=httpx.MockTransport(repondre))


def test_evaluate_case_get_reussi_quand_le_nombre_correspond():
    case = {"methode": "GET", "description": "Total", "chemin": "/regles", "nombre_attendu": 245}

    resultat = evaluate_case(_client_get_mock(245), "http://localhost:8880", case)

    assert resultat["reussi"] is True
    assert resultat["description"] == "Total"


def test_evaluate_case_get_echoue_quand_le_nombre_differe():
    case = {"methode": "GET", "description": "Total", "chemin": "/regles", "nombre_attendu": 245}

    resultat = evaluate_case(_client_get_mock(240), "http://localhost:8880", case)

    assert resultat["reussi"] is False


def _client_patch_mock(code_reponse: int) -> httpx.Client:
    def repondre(requete: httpx.Request) -> httpx.Response:
        return httpx.Response(code_reponse)

    return httpx.Client(transport=httpx.MockTransport(repondre))


def test_evaluate_case_patch_reussi_quand_le_code_correspond():
    case = {
        "methode": "PATCH",
        "description": "Refus sans jeton",
        "chemin": "/regles/1",
        "jeton": None,
        "corps": {"review_status": None},
        "code_attendu": 401,
    }

    resultat = evaluate_case(_client_patch_mock(401), "http://localhost:8880", case)

    assert resultat["reussi"] is True


def test_evaluate_case_patch_echoue_quand_le_code_differe():
    case = {
        "methode": "PATCH",
        "description": "Refus sans jeton",
        "chemin": "/regles/1",
        "jeton": None,
        "corps": {"review_status": None},
        "code_attendu": 401,
    }

    resultat = evaluate_case(_client_patch_mock(200), "http://localhost:8880", case)

    assert resultat["reussi"] is False


def test_evaluate_case_patch_avec_jeton_dun_client_nomme(monkeypatch):
    """jeton: <nom_client> ajoute le Bearer réel de ce client précis."""
    _un_seul_client(monkeypatch)
    monkeypatch.setenv("FASTAPI_API_KEY", "jeton-de-test")
    entetes_recues = {}

    def repondre(requete: httpx.Request) -> httpx.Response:
        entetes_recues.update(requete.headers)
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(repondre))
    case = {
        "methode": "PATCH",
        "description": "Avec jeton dev",
        "chemin": "/regles/1",
        "jeton": "dev",
        "corps": {"review_status": None},
        "code_attendu": 200,
    }

    evaluate_case(client, "http://localhost:8880", case)

    assert entetes_recues["authorization"] == "Bearer jeton-de-test"


def test_evaluate_case_patch_avec_jeton_invalide_envoie_un_faux_bearer():
    """jeton: "invalide" envoie un Bearer erroné, sans lire aucun secret réel."""
    entetes_recues = {}

    def repondre(requete: httpx.Request) -> httpx.Response:
        entetes_recues.update(requete.headers)
        return httpx.Response(401)

    client = httpx.Client(transport=httpx.MockTransport(repondre))
    case = {
        "methode": "PATCH",
        "description": "Jeton invalide",
        "chemin": "/regles/1",
        "jeton": "invalide",
        "corps": {"review_status": None},
        "code_attendu": 401,
    }

    resultat = evaluate_case(client, "http://localhost:8880", case)

    assert resultat["reussi"] is True
    assert entetes_recues["authorization"].startswith("Bearer ")
    assert "jeton-de-test" not in entetes_recues["authorization"]


def test_is_acceptable_vrai_si_tous_les_cas_reussissent():
    evaluations = [{"reussi": True}, {"reussi": True}]

    assert is_acceptable(evaluations) is True


def test_is_acceptable_faux_si_un_seul_cas_echoue():
    """Contrairement au RAG, aucune tolérance : le référentiel est figé."""
    evaluations = [{"reussi": True}, {"reussi": False}]

    assert is_acceptable(evaluations) is False
