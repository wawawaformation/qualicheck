"""
Tests unitaires pour app/api_regles/acceptance.py

Logique pure (load_cases, is_acceptable) et evaluate_case/
verifier_patch_sans_token_refuse mockés via httpx.MockTransport — aucun
appel réseau réel ni API démarrée ici. La suite complète, contre l'API
réellement démarrée, est validée par exécution réelle via
`make api-regles-acceptance`.
"""

import httpx

from app.api_regles.acceptance import (
    evaluate_case,
    is_acceptable,
    load_cases,
    verifier_patch_sans_token_refuse,
)


def test_load_cases_parses_jsonl(tmp_path):
    """load_cases lit un fichier JSONL, une entrée par ligne."""
    jsonl_path = tmp_path / "cases.jsonl"
    jsonl_path.write_text(
        '{"description": "D1", "chemin": "/regles", "nombre_attendu": 245}\n'
        '{"description": "D2", "chemin": "/regles?outil=manuel", "nombre_attendu": 44}\n',
        encoding="utf-8",
    )

    cases = load_cases(jsonl_path)

    assert cases == [
        {"description": "D1", "chemin": "/regles", "nombre_attendu": 245},
        {"description": "D2", "chemin": "/regles?outil=manuel", "nombre_attendu": 44},
    ]


def _client_mock(nombre_regles: int) -> httpx.Client:
    """Client httpx dont le transport renvoie une liste factice de N règles."""

    def repondre(requete: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"numero": i} for i in range(nombre_regles)])

    return httpx.Client(transport=httpx.MockTransport(repondre))


def test_evaluate_case_reussi_quand_le_nombre_correspond():
    case = {"description": "Total", "chemin": "/regles", "nombre_attendu": 245}

    resultat = evaluate_case(_client_mock(245), "http://localhost:8880", case)

    assert resultat["reussi"] is True
    assert resultat["nombre_retourne"] == 245
    assert resultat["description"] == "Total"


def test_evaluate_case_echoue_quand_le_nombre_differe():
    case = {"description": "Total", "chemin": "/regles", "nombre_attendu": 245}

    resultat = evaluate_case(_client_mock(240), "http://localhost:8880", case)

    assert resultat["reussi"] is False
    assert resultat["nombre_retourne"] == 240


def test_is_acceptable_vrai_si_tous_les_cas_reussissent():
    evaluations = [{"reussi": True}, {"reussi": True}]

    assert is_acceptable(evaluations) is True


def test_is_acceptable_faux_si_un_seul_cas_echoue():
    """Contrairement au RAG, aucune tolérance : le référentiel est figé."""
    evaluations = [{"reussi": True}, {"reussi": False}]

    assert is_acceptable(evaluations) is False


def test_verifier_patch_sans_token_refuse_vrai_si_401():
    def repondre(requete: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = httpx.Client(transport=httpx.MockTransport(repondre))

    assert verifier_patch_sans_token_refuse(client, "http://localhost:8880") is True


def test_verifier_patch_sans_token_refuse_faux_si_pas_401():
    def repondre(requete: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"numero": 1})

    client = httpx.Client(transport=httpx.MockTransport(repondre))

    assert verifier_patch_sans_token_refuse(client, "http://localhost:8880") is False
