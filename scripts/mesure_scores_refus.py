"""Mesure les scores de similarité (top-1, écart top-1/top-15) pour trancher
si un seuil relatif sépare les cas sans_reponse des cas PASS.

Rejoue tests/acceptance/rag_acceptance.jsonl (coût réel : décomposition LLM
+ embedding), calcule metriques_scores() par cas, puis compare les
distributions entre la famille sans_reponse et les cas jugés PASS par
evaluate_case() (les autres familles). Produit un rapport Markdown
horodaté dans docs/eval/. Voir
docs/superpowers/specs/2026-09-11-retrieval-refus-design.md (Temps 1).

Volontairement hors CI, comme rag_dense_acceptance.py — lancé à la demande
via `make mesure-scores-refus`.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    evaluate_case,
    load_cases,
    metriques_scores,
)
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402
from app.retrieval.retrieval import retrieve  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

FAMILLE_SANS_REPONSE = "sans_reponse"


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def _resume(valeurs: list[float]) -> dict:
    """Min/max/moyenne d'une liste de scores, pour comparer deux groupes."""
    return {
        "min": min(valeurs),
        "max": max(valeurs),
        "moyenne": sum(valeurs) / len(valeurs),
        "n": len(valeurs),
    }


def build_report(mesures: list[dict], horodatage: datetime) -> str:
    """Compare les distributions top1/top15/ecart entre sans_reponse et PASS."""
    sans_reponse = [m for m in mesures if m["famille"] == FAMILLE_SANS_REPONSE]
    pass_cases = [
        m for m in mesures if m["famille"] != FAMILLE_SANS_REPONSE and m["verdict"] == "PASS"
    ]

    lignes = [
        f"# Mesure des scores — refus du retrieval ({horodatage.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"`sans_reponse` : {len(sans_reponse)} cas — cas `PASS` (autres familles) : "
        f"{len(pass_cases)} cas",
        "",
        "## Distributions par métrique",
        "",
        "| Métrique | Groupe | min | max | moyenne |",
        "|---|---|---|---|---|",
    ]
    for metrique in ("top1", "top15", "ecart"):
        for nom_groupe, groupe in (("sans_reponse", sans_reponse), ("PASS", pass_cases)):
            stats = _resume([m[metrique] for m in groupe])
            lignes.append(
                f"| {metrique} | {nom_groupe} | {stats['min']:.3f} | {stats['max']:.3f} | "
                f"{stats['moyenne']:.3f} |"
            )

    lignes.append("")
    lignes.append("## Détail par cas")
    lignes.append("")
    lignes.append("| Famille | Verdict | top1 | top15 | écart | Question |")
    lignes.append("|---|---|---|---|---|---|")
    for m in mesures:
        lignes.append(
            f"| {m['famille']} | {m['verdict']} | {m['top1']:.3f} | {m['top15']:.3f} | "
            f"{m['ecart']:.3f} | {m['question']} |"
        )

    return "\n".join(lignes) + "\n"


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)
    embedding_client = EmbeddingClient()
    decomposition_client = DecompositionClient()

    logger.info("=== mesure_scores_refus : démarrage ===")
    progress_logger.info("=== mesure_scores_refus : démarrage ===")

    mesures = []
    with Session(engine) as session:
        for case in cases:
            resultat = retrieve(
                session=session,
                question=case["question"],
                top_n=15,
                decomposition_client=decomposition_client,
                embedding_client=embedding_client,
            )
            numeros = [numero for numero, _ in resultat]
            evaluation = evaluate_case(case, numeros)
            metriques = metriques_scores(resultat)
            mesures.append(
                {
                    "question": case["question"],
                    "famille": case["famille"],
                    "verdict": evaluation["verdict"],
                    **metriques,
                }
            )
            progress_logger.info(
                f"mesure_scores_refus — « {case['question']} » [{case['famille']}] "
                f"{evaluation['verdict']} — top1={metriques['top1']:.3f} "
                f"top15={metriques['top15']:.3f}"
            )

    horodatage = datetime.now()
    rapport = build_report(mesures, horodatage)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"mesure_scores_refus_{horodatage.strftime('%Y-%m-%d_%H%M%S')}.md"
    report_path.write_text(rapport, encoding="utf-8")

    logger.info(f"=== mesure_scores_refus : rapport écrit dans {report_path} ===")
    progress_logger.info(f"=== mesure_scores_refus : rapport écrit dans {report_path} ===")


if __name__ == "__main__":
    main()
