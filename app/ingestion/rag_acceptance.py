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


def query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[tuple[int, float]]:
    """Retourne les (numéro, score) des top_n règles les plus proches du vecteur.

    Score de similarité cosinus (1 - distance) : 1 = identique, 0 = aucun
    rapport. Ordonné par similarité décroissante (le plus proche en premier).
    """
    resultats = (
        session.query(Regle.numero, Regle.embedding.cosine_distance(vector))
        .order_by(Regle.embedding.cosine_distance(vector))
        .limit(top_n)
        .all()
    )
    return [(numero, 1 - distance) for numero, distance in resultats]


def metriques_scores(candidats: list[tuple[int, float]]) -> dict:
    """Calcule top1 (meilleur score) et top15 (15e meilleur, ou le dernier si moins de 15).

    Trie localement par score décroissant, indépendamment de l'ordre de la
    liste passée (retrieve() ordonne par première apparition entre
    sous-questions, pas par score).
    """
    tries = sorted(candidats, key=lambda c: c[1], reverse=True)
    top1 = tries[0][1]
    index_top15 = min(14, len(tries) - 1)
    top15 = tries[index_top15][1]
    return {"top1": top1, "top15": top15, "ecart": top1 - top15}


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


def compute_taux_par_famille(evaluations: list[dict]) -> dict[str, dict]:
    """Calcule le taux de réussite par famille, en excluant les PARTIEL.

    Un cas PARTIEL ne compte ni comme succès ni comme échec : il est
    retiré du dénominateur pour ne pas fausser le taux binaire, mais son
    nombre est conservé (partiels) pour rester visible dans les logs.
    Une famille sans aucun cas PASS/FAIL (uniquement des PARTIEL) a un
    taux de 0.0 par convention — pas de division par zéro.
    """
    par_famille: dict[str, list[dict]] = {}
    for evaluation in evaluations:
        par_famille.setdefault(evaluation["famille"], []).append(evaluation)

    resultat = {}
    for famille, evals in par_famille.items():
        partiels = sum(1 for e in evals if e["verdict"] == "PARTIEL")
        non_partiels = [e for e in evals if e["verdict"] != "PARTIEL"]
        reussis = sum(1 for e in non_partiels if e["verdict"] == "PASS")
        total = len(non_partiels)
        taux = reussis / total if total > 0 else 0.0
        resultat[famille] = {"taux": taux, "reussis": reussis, "total": total, "partiels": partiels}
    return resultat


def is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool:
    """Le jeu est acceptable si chaque famille à cible normale atteint le seuil.

    La famille "sans_reponse" est toujours ignorée : son taux est nul par
    construction (aucun mécanisme de refus), ce n'est pas un défaut du
    retrieval mesuré par les autres familles.
    """
    for famille, stats in taux_par_famille.items():
        if famille == "sans_reponse":
            continue
        if stats["taux"] < seuil:
            return False
    return True


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
