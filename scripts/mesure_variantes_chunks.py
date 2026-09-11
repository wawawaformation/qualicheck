"""Mesure MRR et recall@k pour 12 variantes de chunk (11 champs isolés +
le chunk complet de production comme baseline) sur les 114 cas
d'acceptance — vague 1 du protocole de mesure des chunks. Voir
docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md.

Aucune écriture dans regle.embedding : tous les vecteurs des variantes
restent en mémoire, la similarité est calculée en numpy (pas de requête
SQL pgvector). Décomposition et embedding des 114 questions calculés une
seule fois, réutilisés pour les 12 variantes.

Coût réel (~0,011 €), volontairement hors CI — lancé à la demande via
`make mesure-variantes-chunks`.
"""

import csv
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
    construire_resume_markdown,
    load_cases,
    mesurer_variante,
)
from app.ingestion.stockage import load_enriched_rules_from_db  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

BATCH_SIZE = 50
TOP_N = 15
RECALL_KS = [1, 3, 5, 10, 15]

CHAMPS_ISOLES = [
    "intitule",
    "theme",
    "contexte",
    "solution",
    "controle",
    "objectifs",
    "tags",
    "phases",
    "strategie_analyse",
    "strategie_justification",
    "guide_analyse",
]


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def vectoriser_variante(regles, champ: str | None, embedding_client: EmbeddingClient) -> dict:
    """Construit le texte de chaque règle pour une variante puis vectorise
    par lots de BATCH_SIZE. champ=None signifie la baseline
    (build_chunk_text). Règles à texte vide exclues (pas de texte envoyé
    à l'API)."""
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
        # rencontré en exécution réelle le 2026-09-11 — quota vraisemblablement
        # en tokens/minute (déclenché par les lots de chunk complet, le texte
        # le plus long des 12 variantes), pas juste en nombre de requêtes.
        # Azure suggérait d'attendre jusqu'à 19s ; le retry existant
        # (backoff max 8s) ne suffisait pas. 2s puis 20s testés en pratique.
        time.sleep(20)

    return vecteurs_regles


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    # cibles_mesurees : sous-ensemble de numeros_attendus effectivement
    # vectorisé pour la variante (ex. une règle sans tag est absente de
    # cette liste pour la variante "tags") — sert au calcul du MRR/recall,
    # exposé ici pour que le CSV soit reproductible sans deviner l'exclusion.
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "variante",
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


def ecrire_resume_markdown(chemin: Path, lignes: list[dict], horodatage: datetime) -> None:
    chemin.write_text(construire_resume_markdown(lignes, horodatage), encoding="utf-8")


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)

    logger.info("=== mesure_variantes_chunks : démarrage ===")
    progress_logger.info("=== mesure_variantes_chunks : démarrage ===")

    with Session(engine) as session:
        enriched_rules = load_enriched_rules_from_db(session)
    regles = enriched_rules.regles

    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    # Décomposition + embedding des 114 questions, une seule fois — figés
    # et réutilisés pour les 12 variantes.
    sous_questions_vecteurs_par_cas = []
    for case in cases:
        sous_questions = decomposition_client.decomposer(case["question"])
        vecteurs = embedding_client.embed_batch(sous_questions)
        sous_questions_vecteurs_par_cas.append(vecteurs)

    progress_logger.info(
        f"mesure_variantes_chunks — décomposition des {len(cases)} cas terminée "
        f"({decomposition_client.input_tokens}+{decomposition_client.output_tokens} tokens)"
    )

    toutes_lignes_csv = []
    tous_lignes_resume = []

    variantes = [("baseline", None)] + [(champ, champ) for champ in CHAMPS_ISOLES]

    for nom_variante, champ in variantes:
        vecteurs_regles = vectoriser_variante(regles, champ, embedding_client)
        progress_logger.info(
            f"mesure_variantes_chunks — variante {nom_variante} : "
            f"{len(vecteurs_regles)}/{len(regles)} règles vectorisées"
        )

        lignes_csv, lignes_resume = mesurer_variante(
            nom_variante, vecteurs_regles, cases, sous_questions_vecteurs_par_cas, TOP_N, RECALL_KS
        )
        for ligne in lignes_resume:
            progress_logger.info(
                f"mesure_variantes_chunks — {nom_variante} / {ligne['famille']} : "
                f"MRR={ligne['mrr']:.3f} recall@5={ligne['recall_5']:.3f}"
            )
        toutes_lignes_csv.extend(lignes_csv)
        tous_lignes_resume.extend(lignes_resume)

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")

    csv_path = REPORT_DIR / f"mesure_variantes_chunks_{suffixe}.csv"
    ecrire_csv(csv_path, toutes_lignes_csv)

    md_path = REPORT_DIR / f"mesure_variantes_chunks_{suffixe}.md"
    ecrire_resume_markdown(md_path, tous_lignes_resume, horodatage)

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
        f"mesure_variantes_chunks — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)

    logger.info(f"=== mesure_variantes_chunks : rapports écrits dans {csv_path} et {md_path} ===")
    progress_logger.info(
        f"=== mesure_variantes_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )


if __name__ == "__main__":
    main()
