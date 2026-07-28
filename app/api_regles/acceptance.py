"""
Jeu d'acceptance de l'API données : vérifie les endpoints réels contre le
vrai référentiel Opquast (245 règles), sur le modèle de
app/ingestion/rag_acceptance.py.

Nécessite l'API réellement démarrée (make api-regles) — appels HTTP réels,
pas de TestClient : c'est le service tel qu'il tournera en pratique qui est
vérifié, pas une simulation en mémoire.
"""

import json
from pathlib import Path

import httpx


def load_cases(jsonl_path: Path) -> list[dict]:
    """Charge le jeu de cas d'acceptance depuis un fichier JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate_case(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Évalue un cas : le nombre de règles retourné correspond-il à l'attendu ?"""
    reponse = client.get(f"{base_url}{case['chemin']}", timeout=10)
    reponse.raise_for_status()
    nombre_retourne = len(reponse.json())
    return {
        "description": case["description"],
        "chemin": case["chemin"],
        "nombre_attendu": case["nombre_attendu"],
        "nombre_retourne": nombre_retourne,
        "reussi": nombre_retourne == case["nombre_attendu"],
    }


def is_acceptable(evaluations: list[dict]) -> bool:
    """
    Le référentiel Opquast est figé (245 règles connues) : contrairement au
    RAG sémantique, aucune tolérance n'est accordée — un seul cas en échec
    fait échouer toute la suite.
    """
    return all(evaluation["reussi"] for evaluation in evaluations)


def verifier_patch_sans_token_refuse(client: httpx.Client, base_url: str) -> bool:
    """Un PATCH sans jeton Bearer doit être refusé (401)."""
    reponse = client.patch(
        f"{base_url}/regles/1", json={"review_status": None}, timeout=10
    )
    return reponse.status_code == 401
