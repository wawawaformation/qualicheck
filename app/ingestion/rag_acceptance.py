"""
Jeu d'acceptance RAG : vérifie que la recherche sémantique pgvector
retrouve la bonne règle Opquast pour une question en langage naturel.

Formalise les vérifications manuelles du 2026-07-26 — voir
docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.referentiel import Regle


def load_cases(jsonl_path: Path) -> list[dict]:
    """Charge le jeu de cas d'acceptance RAG depuis un fichier JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[int]:
    """Retourne les numéros des top_n règles les plus proches du vecteur (similarité cosinus)."""
    resultats = (
        session.query(Regle.numero)
        .order_by(Regle.embedding.cosine_distance(vector))
        .limit(top_n)
        .all()
    )
    return [numero for (numero,) in resultats]


def evaluate_case(case: dict, numeros_retournes: list[int]) -> dict:
    """Évalue un cas : la règle attendue figure-t-elle dans les résultats retournés ?"""
    return {
        "question": case["question"],
        "numero_regle_attendue": case["numero_regle_attendue"],
        "numeros_retournes": numeros_retournes,
        "reussi": case["numero_regle_attendue"] in numeros_retournes,
    }


def compute_taux_reussite(evaluations: list[dict]) -> float:
    """Calcule la proportion de cas réussis parmi les évaluations."""
    return sum(1 for e in evaluations if e["reussi"]) / len(evaluations)


def is_acceptable(taux: float, seuil: float) -> bool:
    """Le taux de réussite global atteint-il le seuil minimum déclaré dans le manifest ?"""
    return taux >= seuil
