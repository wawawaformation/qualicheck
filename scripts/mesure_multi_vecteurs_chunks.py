"""Mesure MRR et recall@k pour un candidat à 3 vecteurs par règle (chunk
complet + intitulé seul + guide_analyse seul, fusionnés à la requête en
gardant le meilleur score par règle) contre la baseline — vague 3 du
protocole de mesure des chunks. Réutilise le jeu réservé et le critère
de décision déjà actés en vague 2. Voir
docs/superpowers/specs/2026-09-11-mesure-chunks-vague3-design.md.

Aucune écriture dans regle.embedding : tous les vecteurs restent en
mémoire, la similarité est calculée en numpy (pas de requête SQL
pgvector). Décomposition et embedding des 114 questions calculés une
seule fois.

Coût réel estimé 0,010-0,015 €, volontairement hors CI — lancé à la
demande via `make mesure-multi-vecteurs-chunks`.
"""

import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunking import build_chunk_text, build_variant_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    appliquer_critere_decision,
    construire_resume_markdown_vague2,
    load_cases,
    mesurer_candidat_fusion,
    mesurer_variante,
)
from app.ingestion.stockage import load_enriched_rules_from_db  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
HOLDOUT_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance_holdout.json"
)
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

BATCH_SIZE = 50
TOP_N = 15
RECALL_KS = [1, 3, 5, 10, 15]
NOM_CANDIDAT_FUSION = "F_multi_vecteurs"

# type de vecteur -> champ (None = baseline, build_chunk_text)
TYPES_VECTEURS = {
    "baseline": None,
    "intitule": "intitule",
    "guide_analyse": "guide_analyse",
}


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def charger_jeu_reserve_existant(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    """Charge le jeu réservé déjà figé par la vague 2
    (tests/acceptance/rag_acceptance_holdout.json) — ne le tire jamais.
    Ce fichier doit déjà exister (vague 2 exécutée avant cette vague)."""
    if not HOLDOUT_PATH.exists():
        raise FileNotFoundError(
            f"{HOLDOUT_PATH} introuvable — la vague 2 "
            "(make mesure-combinaisons-chunks) doit avoir été exécutée "
            "au moins une fois avant cette vague."
        )
    questions_reserve = set(json.loads(HOLDOUT_PATH.read_text(encoding="utf-8")))
    reserve = [c for c in cases if c["question"] in questions_reserve]
    exploration = [c for c in cases if c["question"] not in questions_reserve]
    return exploration, reserve


def vectoriser_type(
    regles, champ: str | None, embedding_client: EmbeddingClient
) -> dict[int, list[float]]:
    """Construit le texte de chaque règle pour un type de vecteur (baseline
    si champ=None, sinon un champ isolé via build_variant_text) puis
    vectorise par lots de BATCH_SIZE."""
    textes_par_numero = {}
    for rule in regles:
        texte = build_chunk_text(rule) if champ is None else build_variant_text(rule, champ)
        if texte is not None:
            textes_par_numero[rule.number] = texte

    numeros_ordonnes = list(textes_par_numero.keys())
    vecteurs_regles: dict[int, list[float]] = {}
    for i in range(0, len(numeros_ordonnes), BATCH_SIZE):
        lot_numeros = numeros_ordonnes[i : i + BATCH_SIZE]
        lot_textes = [textes_par_numero[n] for n in lot_numeros]
        lot_vecteurs = embedding_client.embed_batch(lot_textes)
        for numero, vecteur in zip(lot_numeros, lot_vecteurs, strict=True):
            vecteurs_regles[numero] = vecteur
        # Pause entre lots : évite le RateLimitReached Azure (tier S0),
        # rencontré lors de la vague 1 (scripts/mesure_variantes_chunks.py).
        time.sleep(20)

    return vecteurs_regles


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "variante",
                "sous_ensemble",
                "question",
                "famille",
                "numeros_attendus",
                "cibles_mesurees",
                "numero_retourne",
                "rang",
                "cosinus",
                "est_cible",
            ],
        )
        writer.writeheader()
        writer.writerows(lignes)


def ecrire_resume_markdown(
    chemin: Path,
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
) -> None:
    chemin.write_text(
        construire_resume_markdown_vague2(
            lignes_exploration,
            lignes_reserve,
            decision,
            horodatage,
            titre="Mesure multi-vecteurs — vague 3",
        ),
        encoding="utf-8",
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)
    exploration_cases, reserve_cases = charger_jeu_reserve_existant(cases)

    logger.info("=== mesure_multi_vecteurs_chunks : démarrage ===")
    progress_logger.info(
        f"mesure_multi_vecteurs_chunks — jeu d'exploration : {len(exploration_cases)} cas, "
        f"jeu réservé : {len(reserve_cases)} cas"
    )

    with Session(engine) as session:
        enriched_rules = load_enriched_rules_from_db(session)
    regles = enriched_rules.regles

    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    vecteurs_par_question: dict[str, list[list[float]]] = {}
    for case in cases:
        sous_questions = decomposition_client.decomposer(case["question"])
        vecteurs_par_question[case["question"]] = embedding_client.embed_batch(sous_questions)

    progress_logger.info(
        f"mesure_multi_vecteurs_chunks — décomposition des {len(cases)} cas terminée "
        f"({decomposition_client.input_tokens}+{decomposition_client.output_tokens} tokens)"
    )

    vecteurs_par_type: dict[str, dict[int, list[float]]] = {}
    for nom_type, champ in TYPES_VECTEURS.items():
        vecteurs_par_type[nom_type] = vectoriser_type(regles, champ, embedding_client)
        progress_logger.info(
            f"mesure_multi_vecteurs_chunks — type {nom_type} : "
            f"{len(vecteurs_par_type[nom_type])}/{len(regles)} règles vectorisées"
        )

    vecteurs_exploration = [vecteurs_par_question[c["question"]] for c in exploration_cases]
    vecteurs_reserve = [vecteurs_par_question[c["question"]] for c in reserve_cases]

    lignes_csv_baseline_exploration, lignes_resume_baseline_exploration = mesurer_variante(
        "baseline",
        vecteurs_par_type["baseline"],
        exploration_cases,
        vecteurs_exploration,
        TOP_N,
        RECALL_KS,
    )
    lignes_csv_baseline_reserve, lignes_resume_baseline_reserve = mesurer_variante(
        "baseline", vecteurs_par_type["baseline"], reserve_cases, vecteurs_reserve, TOP_N, RECALL_KS
    )

    lignes_csv_fusion_exploration, lignes_resume_fusion_exploration = mesurer_candidat_fusion(
        NOM_CANDIDAT_FUSION,
        vecteurs_par_type,
        exploration_cases,
        vecteurs_exploration,
        TOP_N,
        RECALL_KS,
    )
    lignes_csv_fusion_reserve, lignes_resume_fusion_reserve = mesurer_candidat_fusion(
        NOM_CANDIDAT_FUSION, vecteurs_par_type, reserve_cases, vecteurs_reserve, TOP_N, RECALL_KS
    )

    for ligne in lignes_csv_baseline_exploration:
        ligne["sous_ensemble"] = "exploration"
    for ligne in lignes_csv_baseline_reserve:
        ligne["sous_ensemble"] = "reserve"
    for ligne in lignes_csv_fusion_exploration:
        ligne["sous_ensemble"] = "exploration"
    for ligne in lignes_csv_fusion_reserve:
        ligne["sous_ensemble"] = "reserve"

    toutes_lignes_csv = (
        lignes_csv_baseline_exploration
        + lignes_csv_baseline_reserve
        + lignes_csv_fusion_exploration
        + lignes_csv_fusion_reserve
    )

    mrr_exploration = {
        "baseline": {
            ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_baseline_exploration
        },
        NOM_CANDIDAT_FUSION: {
            ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_fusion_exploration
        },
    }
    mrr_reserve = {
        "baseline": {ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_baseline_reserve},
        NOM_CANDIDAT_FUSION: {
            ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_fusion_reserve
        },
    }
    decision = appliquer_critere_decision(mrr_exploration, mrr_reserve)
    progress_logger.info(f"mesure_multi_vecteurs_chunks — décision : {decision}")

    tous_lignes_resume_exploration = (
        lignes_resume_baseline_exploration + lignes_resume_fusion_exploration
    )
    tous_lignes_resume_reserve = lignes_resume_baseline_reserve + lignes_resume_fusion_reserve

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")

    csv_path = REPORT_DIR / f"mesure_multi_vecteurs_chunks_{suffixe}.csv"
    ecrire_csv(csv_path, toutes_lignes_csv)

    md_path = REPORT_DIR / f"mesure_multi_vecteurs_chunks_{suffixe}.md"
    ecrire_resume_markdown(
        md_path, tous_lignes_resume_exploration, tous_lignes_resume_reserve, decision, horodatage
    )

    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
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
    summary = (
        f"mesure_multi_vecteurs_chunks — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)

    logger.info(
        f"=== mesure_multi_vecteurs_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )
    progress_logger.info(
        f"=== mesure_multi_vecteurs_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )


if __name__ == "__main__":
    main()
