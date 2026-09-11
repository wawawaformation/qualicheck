"""Mesure si un LLM classe correctement une question dans/hors périmètre
Opquast SANS voir de candidats retrieval — teste l'hypothèse que le biais
de sélection mesuré sur le jugement LLM (Temps 2, `app/retrieval/jugement.py`)
vient de la présence même des candidats, pas d'une incapacité générale à
juger. Rejoue les 114 cas d'acceptance (`tests/acceptance/rag_acceptance.jsonl`) :
attendu = dans le périmètre pour toute famille à cible, hors périmètre pour
`sans_reponse`. Aucun retrieval, aucune décomposition, aucun embedding —
un seul appel `GuardrailClient` par cas.

Coût réel (114 appels `gpt-5.4-mini`, ~0,003-0,005 €), volontairement hors
CI — lancé à la demande via `make mesure-guardrail-perimetre`. Voir
docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import load_cases  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.guardrail import GuardrailClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

FAMILLE_SANS_REPONSE = "sans_reponse"


def main() -> None:
    setup_logging()
    load_dotenv()

    cases = load_cases(CASES_PATH)
    client = GuardrailClient()

    logger.info("=== mesure_guardrail_perimetre : démarrage ===")
    progress_logger.info("=== mesure_guardrail_perimetre : démarrage ===")

    resultats = []
    for case in cases:
        attendu_dans_perimetre = case["famille"] != FAMILLE_SANS_REPONSE
        classe_dans_perimetre = client.est_dans_le_perimetre(case["question"])
        correct = classe_dans_perimetre == attendu_dans_perimetre

        resultats.append(
            {
                "question": case["question"],
                "famille": case["famille"],
                "attendu_dans_perimetre": attendu_dans_perimetre,
                "classe_dans_perimetre": classe_dans_perimetre,
                "correct": correct,
            }
        )
        progress_logger.info(
            f"mesure_guardrail_perimetre — « {case['question']} » "
            f"[{case['famille']}] (attendu dans_perimetre={attendu_dans_perimetre}, "
            f"classé={classe_dans_perimetre}) — {'OK' if correct else 'ERREUR'}"
        )

    par_famille: dict[str, list[dict]] = {}
    for r in resultats:
        par_famille.setdefault(r["famille"], []).append(r)

    lignes_resume = []
    for famille, lignes in par_famille.items():
        corrects = sum(1 for ligne in lignes if ligne["correct"])
        taux = corrects / len(lignes)
        lignes_resume.append({"famille": famille, "corrects": corrects, "total": len(lignes)})
        progress_logger.info(
            f"mesure_guardrail_perimetre — famille {famille} : "
            f"{corrects}/{len(lignes)} ({taux:.0%})"
        )

    # Vue spécifique demandée : faux refus (question valide classée hors
    # périmètre) vs faux positifs (sans_reponse classée dans le périmètre) —
    # les deux ne sont pas équivalents en gravité (un faux refus bloque une
    # vraie question, un faux positif se rattrape encore via le jugement).
    faux_refus = [
        r for r in resultats if r["attendu_dans_perimetre"] and not r["classe_dans_perimetre"]
    ]
    faux_positifs = [
        r for r in resultats if not r["attendu_dans_perimetre"] and r["classe_dans_perimetre"]
    ]
    progress_logger.info(
        f"mesure_guardrail_perimetre — faux refus (question valide écartée) : "
        f"{len(faux_refus)} ; faux positifs (sans_reponse laissée passer) : {len(faux_positifs)}"
    )

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")
    md_path = REPORT_DIR / f"mesure_guardrail_perimetre_{suffixe}.md"

    entete = "| Famille | Corrects | Total | Taux |"
    separateur = "|---|---|---|---|"
    corps = [
        f"| {r['famille']} | {r['corrects']} | {r['total']} | "
        f"{r['corrects'] / r['total']:.0%} |"
        for r in lignes_resume
    ]
    faux_refus_texte = "\n".join(f"- {r['question']} [{r['famille']}]" for r in faux_refus) or (
        "aucun"
    )
    faux_positifs_texte = "\n".join(f"- {r['question']}" for r in faux_positifs) or "aucun"
    contenu = (
        f"# Mesure guardrail — classification dans/hors périmètre "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"{entete}\n{separateur}\n" + "\n".join(corps) + "\n\n"
        f"## Faux refus (question valide écartée à tort)\n\n{faux_refus_texte}\n\n"
        f"## Faux positifs (sans_reponse laissée passer à tort)\n\n{faux_positifs_texte}\n"
    )
    md_path.write_text(contenu, encoding="utf-8")

    manifest_role = load_manifest()["guardrail"]
    cost = (
        client.input_tokens * manifest_role["prix_entree_par_million"] / 1_000_000
        + client.output_tokens * manifest_role["prix_sortie_par_million"] / 1_000_000
    )
    summary = (
        f"mesure_guardrail_perimetre — tokens : {client.input_tokens}+{client.output_tokens}, "
        f"coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)
    logger.info(f"=== mesure_guardrail_perimetre : rapport écrit dans {md_path} ===")
    progress_logger.info(f"=== mesure_guardrail_perimetre : rapport écrit dans {md_path} ===")


if __name__ == "__main__":
    main()
