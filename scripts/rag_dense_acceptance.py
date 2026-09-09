"""Compare le recall du RAG sur plusieurs top_n (3/5/10/15) en une exécution.

Rejoue tests/acceptance/rag_acceptance.jsonl une seule fois (un seul appel
API embeddings, une seule requête pgvector par question à LIMIT 15), puis
tronque localement pour chaque top_n de TOP_NS. Produit un rapport Markdown
horodaté dans docs/eval/. Exploration ponctuelle, distincte de l'instrument
de mesure officiel de l'Étape 3 (scripts/check_rag_acceptance.py, inchangé)
— voir docs/superpowers/specs/2026-09-09-rag-dense-acceptance-design.md.
"""

import logging
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    evaluate_case,
    load_cases,
    query_top_n_numeros,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

TOP_NS = [3, 5, 10, 15]


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def build_report(taux_par_top_n: dict[int, dict], evaluations_top15: list[dict]) -> str:
    """Construit le rapport Markdown : tableau agrégé + cas PARTIEL/FAIL à top_n=15."""
    familles = list(taux_par_top_n[TOP_NS[0]].keys())

    entete = "| Famille | " + " | ".join(f"top_n={n}" for n in TOP_NS) + " |"
    separateur = "|---|" + "|".join("---" for _ in TOP_NS) + "|"
    lignes = [entete, separateur]
    for famille in familles:
        valeurs = [f"{taux_par_top_n[n][famille]['taux']:.0%}" for n in TOP_NS]
        lignes.append(f"| {famille} | " + " | ".join(valeurs) + " |")
    tableau = "\n".join(lignes)

    echecs = [e for e in evaluations_top15 if e["verdict"] in ("FAIL", "PARTIEL")]
    lignes_echecs = [
        f"- **{e['verdict']}** [{e['famille']}] « {e['question']} » — "
        f"attendu {e['numeros_regle_attendus']}, retourné {e['numeros_retournes']}"
        for e in echecs
    ]
    section_echecs = "\n".join(lignes_echecs) if lignes_echecs else "Aucun."

    return (
        f"# Mesure recall — rag_dense_acceptance ({date.today().isoformat()})\n\n"
        f"## Taux de réussite par famille × top_n\n\n{tableau}\n\n"
        f"## Cas PARTIEL/FAIL persistants à top_n=15\n\n{section_echecs}\n"
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    top_n_max = max(TOP_NS)

    logger.info("=== rag_dense_acceptance : démarrage ===")
    progress_logger.info("=== rag_dense_acceptance : démarrage ===")

    cases = load_cases(CASES_PATH)
    client = EmbeddingClient()
    vectors = client.embed_batch([case["question"] for case in cases])

    resultats_par_top_n: dict[int, list[dict]] = {n: [] for n in TOP_NS}
    with Session(engine) as session:
        for case, vector in zip(cases, vectors, strict=True):
            numeros_retournes_max = query_top_n_numeros(session, vector, top_n_max)
            for n in TOP_NS:
                evaluation = evaluate_case(case, numeros_retournes_max[:n])
                resultats_par_top_n[n].append(evaluation)
                progress_logger.info(
                    f"rag_dense_acceptance — « {case['question']} » "
                    f"[{case['famille']}] top_n={n} — {evaluation['verdict']}"
                )

    taux_par_top_n = {n: compute_taux_par_famille(resultats_par_top_n[n]) for n in TOP_NS}

    role = load_manifest()["embedding"]
    cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
    progress_logger.info(
        f"rag_dense_acceptance — tokens : {client.total_tokens}, coût estimé : {cost:.4f} €"
    )

    rapport = build_report(taux_par_top_n, resultats_par_top_n[top_n_max])
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"rag_dense_acceptance_{date.today().isoformat()}.md"
    report_path.write_text(rapport, encoding="utf-8")

    logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")
    progress_logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")


if __name__ == "__main__":
    main()
