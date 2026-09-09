"""
Jeu d'acceptance RAG : vérifie que la recherche sémantique pgvector
retrouve la bonne règle Opquast pour une question en langage naturel.

Formalise les vérifications manuelles du 2026-07-26 — voir
docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md.
"""

import json
from pathlib import Path

from sqlalchemy import func
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
    """Évalue un cas : verdict PASS/FAIL/PARTIEL selon les cibles retrouvées.

    Un cas sans cible attendue (numeros_regle_attendus vide, famille
    sans_reponse) est toujours FAIL : aucun mécanisme de refus n'existe
    aujourd'hui dans le pipeline de retrieval.
    """
    attendus = case["numeros_regle_attendus"]
    trouves = [n for n in attendus if n in numeros_retournes]

    if not attendus:
        verdict = "FAIL"
    elif len(trouves) == len(attendus):
        verdict = "PASS"
    elif len(trouves) == 0:
        verdict = "FAIL"
    else:
        verdict = "PARTIEL"

    return {
        "question": case["question"],
        "famille": case["famille"],
        "numeros_regle_attendus": attendus,
        "numeros_retournes": numeros_retournes,
        "verdict": verdict,
    }


def compute_taux_reussite(evaluations: list[dict]) -> float:
    """Calcule la proportion de cas réussis parmi les évaluations."""
    return sum(1 for e in evaluations if e["reussi"]) / len(evaluations)


def is_acceptable(taux: float, seuil: float) -> bool:
    """Le taux de réussite global atteint-il le seuil minimum déclaré dans le manifest ?"""
    return taux >= seuil


def summarize_dataset_versions(session: Session) -> list[dict]:
    """Résume la distribution prompt_version/llm_model des règles en base.

    Permet de savoir, au moment d'un run, si le jeu de données est
    homogène (une seule version de prompt) ou mélangé (ex. suite à un
    enrich_again partiel) — information invisible sinon.
    """
    resultats = (
        session.query(Regle.prompt_version, Regle.llm_model, func.count(Regle.id))
        .group_by(Regle.prompt_version, Regle.llm_model)
        .order_by(Regle.prompt_version)
        .all()
    )
    return [
        {"prompt_version": prompt_version, "llm_model": llm_model, "nombre_regles": nombre}
        for prompt_version, llm_model, nombre in resultats
    ]


def format_dataset_versions(summary: list[dict]) -> str:
    """Formate la distribution prompt_version/llm_model pour le log."""
    return " ; ".join(
        f"prompt_version={s['prompt_version']} ({s['llm_model']}): {s['nombre_regles']} règles"
        for s in summary
    )
