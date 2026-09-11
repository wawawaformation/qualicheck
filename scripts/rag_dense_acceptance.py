"""Compare le recall du RAG sur plusieurs top_n (3/5/10/15) en une exécution.

Rejoue tests/acceptance/rag_acceptance.jsonl une seule fois par question
(une seule décomposition, un seul appel API embeddings pour ses
sous-questions, une seule requête pgvector par sous-question à LIMIT 15),
puis tronque localement chaque sous-question pour chaque top_n de TOP_NS
avant de fusionner. Produit un rapport Markdown horodaté dans docs/eval/.

Passe par app.retrieval (décomposition + union), comme l'instrument de
mesure officiel (scripts/check_rag_acceptance.py) depuis le 2026-09-09 —
seule différence : compare plusieurs top_n en un run au lieu d'un seul.
Voir docs/superpowers/specs/2026-09-09-rag-dense-acceptance-design.md et
docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md.
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
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    evaluate_case,
    load_cases,
    query_top_n_numeros,
)
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

TOP_NS = [3, 5, 10, 15]
FAMILLE_HORS_SEUIL = "sans_reponse"


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def retrieve_numeros_par_top_n(
    session: Session,
    question: str,
    top_ns: list[int],
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> dict[int, list[int]]:
    """Retrouve les numéros de règle pour une question, pour chaque top_n.

    Décompose et vectorise une seule fois (indépendant de top_n), interroge
    pgvector une seule fois par sous-question à LIMIT max(top_ns), puis
    pour chaque top_n : tronque le résultat de chaque sous-question à ce
    top_n avant de fusionner (union dédoublonnée, ordre de première
    apparition) — même logique de fusion que app.retrieval.retrieve(),
    sans repayer la décomposition/l'embedding à chaque top_n.
    """
    top_n_max = max(top_ns)
    sous_questions = decomposition_client.decomposer(question)
    vectors = embedding_client.embed_batch(sous_questions)
    numeros_max_par_sous_question = [
        [numero for numero, _ in query_top_n_numeros(session, vector, top_n_max)]
        for vector in vectors
    ]

    resultats: dict[int, list[int]] = {}
    for top_n in top_ns:
        numeros: list[int] = []
        vus: set[int] = set()
        for numeros_max in numeros_max_par_sous_question:
            for numero in numeros_max[:top_n]:
                if numero not in vus:
                    vus.add(numero)
                    numeros.append(numero)
        resultats[top_n] = numeros
    return resultats


def build_report(
    taux_par_top_n: dict[int, dict], evaluations_top15: list[dict], horodatage: datetime
) -> str:
    """Construit le rapport Markdown : tableau agrégé + cas PARTIEL/FAIL à top_n=15."""
    familles = list(taux_par_top_n[TOP_NS[0]].keys())

    entete = "| Famille | " + " | ".join(f"top_n={n}" for n in TOP_NS) + " |"
    separateur = "|---|" + "|".join("---" for _ in TOP_NS) + "|"
    lignes = [entete, separateur]
    for famille in familles:
        valeurs = [f"{taux_par_top_n[n][famille]['taux']:.0%}" for n in TOP_NS]
        lignes.append(f"| {famille} | " + " | ".join(valeurs) + " |")
    tableau = "\n".join(lignes)

    echecs = [
        e
        for e in evaluations_top15
        if e["verdict"] in ("FAIL", "PARTIEL") and e["famille"] != FAMILLE_HORS_SEUIL
    ]
    lignes_echecs = [
        f"- **{e['verdict']}** [{e['famille']}] « {e['question']} » — "
        f"attendu {e['numeros_regle_attendus']}, retourné {e['numeros_retournes']}"
        for e in echecs
    ]
    section_echecs = "\n".join(lignes_echecs) if lignes_echecs else "Aucun."

    return (
        f"# Mesure recall — rag_dense_acceptance ({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"## Taux de réussite par famille × top_n\n\n{tableau}\n\n"
        f"## Cas PARTIEL/FAIL persistants à top_n=15\n\n"
        f"(famille `{FAMILLE_HORS_SEUIL}` exclue : toujours FAIL par construction, "
        f"pas un signal — voir le taux dans le tableau ci-dessus)\n\n{section_echecs}\n"
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    top_n_max = max(TOP_NS)

    logger.info("=== rag_dense_acceptance : démarrage ===")
    progress_logger.info("=== rag_dense_acceptance : démarrage ===")

    cases = load_cases(CASES_PATH)
    embedding_client = EmbeddingClient()
    decomposition_client = DecompositionClient()

    resultats_par_top_n: dict[int, list[dict]] = {n: [] for n in TOP_NS}
    with Session(engine) as session:
        for case in cases:
            numeros_par_top_n = retrieve_numeros_par_top_n(
                session=session,
                question=case["question"],
                top_ns=TOP_NS,
                decomposition_client=decomposition_client,
                embedding_client=embedding_client,
            )
            for n in TOP_NS:
                evaluation = evaluate_case(case, numeros_par_top_n[n])
                resultats_par_top_n[n].append(evaluation)
                progress_logger.info(
                    f"rag_dense_acceptance — « {case['question']} » "
                    f"[{case['famille']}] top_n={n} — {evaluation['verdict']}"
                )

    taux_par_top_n = {n: compute_taux_par_famille(resultats_par_top_n[n]) for n in TOP_NS}

    manifest = load_manifest()
    embedding_role = manifest["embedding"]
    decomposition_role = manifest["decomposition"]
    embedding_cost = (
        embedding_client.total_tokens * embedding_role["prix_entree_par_million"] / 1_000_000
    )
    decomposition_cost = (
        decomposition_client.input_tokens
        * decomposition_role["prix_entree_par_million"]
        / 1_000_000
        + decomposition_client.output_tokens
        * decomposition_role["prix_sortie_par_million"]
        / 1_000_000
    )
    cost = embedding_cost + decomposition_cost
    progress_logger.info(
        f"rag_dense_acceptance — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )

    horodatage = datetime.now()
    rapport = build_report(taux_par_top_n, resultats_par_top_n[top_n_max], horodatage)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"rag_dense_acceptance_{horodatage.strftime('%Y-%m-%d_%H%M%S')}.md"
    report_path.write_text(rapport, encoding="utf-8")

    logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")
    progress_logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")


if __name__ == "__main__":
    main()
