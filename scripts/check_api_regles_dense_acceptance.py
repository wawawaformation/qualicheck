"""Rejoue le jeu d'acceptance RAG via POST /regles/dense en HTTP réel.

Nécessite l'API réellement démarrée (make api-regles, dans un terminal
dédié). Réutilise tests/acceptance/rag_acceptance.jsonl (99 cas, aucune
duplication) : vérifie que le contrat HTTP bout-en-bout produit le même
résultat que l'appel direct à retrieve() (scripts/check_rag_acceptance.py).

Coût réel à chaque exécution (décomposition LLM + embedding pour chaque
cas) — volontairement hors CI, jamais ajouté au jeu automatique
tests/acceptance/api_regles_acceptance.jsonl (rejoué par cd-staging.yml à
chaque déploiement). Lancé à la demande via `make api-regles-dense-acceptance`.
"""

import logging
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_regles import config  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    is_acceptable,
    load_cases,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"


def _entetes() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.clients_tokens()['dev']}"}


def _evaluer_cas_http(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Appelle POST /regles/dense et construit la même structure d'évaluation
    que app.ingestion.rag_acceptance.evaluate_case (verdict PASS/FAIL/PARTIEL)."""
    reponse = client.post(
        f"{base_url}/regles/dense",
        json={"question": case["question"]},
        headers=_entetes(),
        timeout=30,
    )
    reponse.raise_for_status()
    numeros_retournes = [regle["numero"] for regle in reponse.json()]

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


def main() -> None:
    setup_logging()
    load_dotenv()

    base_url = f"http://localhost:{config.PORT}"

    logger.info("=== check_api_regles_dense_acceptance : démarrage ===")
    progress_logger.info("=== check_api_regles_dense_acceptance : démarrage ===")

    try:
        cases = load_cases(CASES_PATH)

        with httpx.Client() as client:
            evaluations = [_evaluer_cas_http(client, base_url, case) for case in cases]
            for evaluation in evaluations:
                progress_logger.info(
                    f"check_api_regles_dense_acceptance — « {evaluation['question']} » "
                    f"[{evaluation['famille']}] (attendu {evaluation['numeros_regle_attendus']}, "
                    f"retourné {evaluation['numeros_retournes']}) — {evaluation['verdict']}"
                )

        taux_par_famille = compute_taux_par_famille(evaluations)
        for famille, stats in taux_par_famille.items():
            partiel_note = f", {stats['partiels']} PARTIEL" if stats["partiels"] else ""
            progress_logger.info(
                f"check_api_regles_dense_acceptance — Famille {famille} : "
                f"{stats['reussis']}/{stats['total']} ({stats['taux']:.0%}){partiel_note}"
            )

    except Exception as e:
        logger.error("check_api_regles_dense_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    seuil = load_manifest()["rag_acceptance"]["taux_reussite_minimum"]
    if not is_acceptable(taux_par_famille, seuil):
        logger.error("check_api_regles_dense_acceptance : au moins une famille sous le seuil")
        sys.exit(1)

    logger.info("=== check_api_regles_dense_acceptance : succès ===")
    progress_logger.info("=== check_api_regles_dense_acceptance : succès ===")


if __name__ == "__main__":
    main()
