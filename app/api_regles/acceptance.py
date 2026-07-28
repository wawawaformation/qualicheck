"""
Jeu d'acceptance de l'API données : vérifie les endpoints réels contre le
vrai référentiel Opquast (245 règles), sur le modèle de
app/ingestion/rag_acceptance.py.

Nécessite l'API réellement démarrée (make api-regles) — appels HTTP réels,
pas de TestClient : c'est le service tel qu'il tournera en pratique qui est
vérifié, pas une simulation en mémoire.

Chaque cas déclare sa méthode (GET ou PATCH) explicitement dans le JSONL :
rien n'est implicite ou codé en dur dans le script.
"""

import json
from pathlib import Path

import httpx

from app.api_regles import config


def load_cases(jsonl_path: Path) -> list[dict]:
    """Charge le jeu de cas d'acceptance depuis un fichier JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _evaluer_get(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Un cas GET compare le nombre de règles retourné à l'attendu."""
    reponse = client.get(f"{base_url}{case['chemin']}", timeout=10)
    reponse.raise_for_status()
    nombre_retourne = len(reponse.json())
    return {
        "description": case["description"],
        "reussi": nombre_retourne == case["nombre_attendu"],
        "detail": f"attendu {case['nombre_attendu']}, obtenu {nombre_retourne}",
    }


def _evaluer_patch(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Un cas PATCH compare le code HTTP retourné à l'attendu."""
    entetes = {}
    if case.get("avec_jeton"):
        entetes["Authorization"] = f"Bearer {config.admin_token()}"

    reponse = client.patch(
        f"{base_url}{case['chemin']}",
        json=case["corps"],
        headers=entetes,
        timeout=10,
    )
    return {
        "description": case["description"],
        "reussi": reponse.status_code == case["code_attendu"],
        "detail": f"attendu {case['code_attendu']}, obtenu {reponse.status_code}",
    }


def evaluate_case(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Dispatche l'évaluation selon la méthode déclarée par le cas."""
    if case["methode"] == "GET":
        return _evaluer_get(client, base_url, case)
    if case["methode"] == "PATCH":
        return _evaluer_patch(client, base_url, case)
    raise ValueError(f"Méthode de cas d'acceptance inconnue : {case['methode']!r}")


def is_acceptable(evaluations: list[dict]) -> bool:
    """
    Le référentiel Opquast est figé (245 règles connues) : contrairement au
    RAG sémantique, aucune tolérance n'est accordée — un seul cas en échec
    fait échouer toute la suite.
    """
    return all(evaluation["reussi"] for evaluation in evaluations)
