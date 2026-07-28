"""Point d'entrée pour rejouer le jeu d'acceptance de l'API données.

Nécessite l'API réellement démarrée (make api-regles, dans un terminal
dédié). Rejoue tests/acceptance/api_regles_acceptance.jsonl (volumes réels
par filtre, authentification du PATCH — chaque cas déclare sa méthode
GET/PATCH explicitement, rien n'est codé en dur), puis vérifie la boucle de
revue de bout en bout (annotation réelle sur une règle, vérifiée par
scripts/enrich_again.py --dry-run, puis annotation retirée).

Aucun appel LLM, aucun coût — un seul PATCH réel sur POSTGRES_DB, réversible,
justifié en exception à la règle POSTGRES_TEST_DB (cf. plan
docs/superpowers/plans/2026-07-26-api-regles-implementation.md, tâche 12).
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_regles import config  # noqa: E402
from app.api_regles.acceptance import evaluate_case, is_acceptable, load_cases  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "api_regles_acceptance.jsonl"
)
PREVIEW_PATH = Path(__file__).resolve().parents[1] / "tmp" / "enrich_again_preview.json"
# Règle utilisée pour vérifier la boucle de revue de bout en bout. Remise à
# son état d'origine (review_status=null) en toute fin de script.
NUMERO_REGLE_BOUCLE_REVUE = 124


def _entetes() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.admin_token()}"}


def _lancer_dry_run() -> None:
    subprocess.run(
        ["uv", "run", "python", "scripts/enrich_again.py", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )


def _preview_contient_la_regle() -> bool:
    """
    enrich_again écrit son aperçu dans tmp/enrich_again_preview.json — les
    logs vont en fichier (app/logging_config.py), pas sur stdout, et le
    fichier n'est PAS réécrit quand aucune règle n'est à revoir (retour
    anticipé dans enrich_again()) : le supprimer avant chaque appel est donc
    indispensable pour ne pas lire un résultat périmé.
    """
    if not PREVIEW_PATH.exists():
        return False
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    return any(entree["numero"] == NUMERO_REGLE_BOUCLE_REVUE for entree in preview)


def _verifier_boucle_revue(client: httpx.Client, base_url: str) -> bool:
    """
    Annote réellement une règle, vérifie que enrich_again --dry-run la
    sélectionne, puis retire l'annotation et vérifie que --dry-run ne
    sélectionne plus rien. Ne dépense jamais d'argent (--dry-run n'appelle
    pas le LLM). Reste hors du JSONL : scénario à plusieurs étapes impliquant
    un sous-processus externe, pas un simple appel HTTP à comparer.
    """
    reponse = client.patch(
        f"{base_url}/regles/{NUMERO_REGLE_BOUCLE_REVUE}",
        json={
            "review_status": "a_revoir",
            "review_note": "Vérification automatique de la boucle de revue (acceptance).",
        },
        headers=_entetes(),
        timeout=10,
    )
    reponse.raise_for_status()

    PREVIEW_PATH.unlink(missing_ok=True)
    _lancer_dry_run()
    selectionnee = _preview_contient_la_regle()

    # Toujours remettre la règle dans son état d'origine, même si la
    # vérification ci-dessus a échoué — sinon le prochain enrich_again réel
    # la corrigerait pour rien.
    reponse_annulation = client.patch(
        f"{base_url}/regles/{NUMERO_REGLE_BOUCLE_REVUE}",
        json={"review_status": None},
        headers=_entetes(),
        timeout=10,
    )
    reponse_annulation.raise_for_status()

    PREVIEW_PATH.unlink(missing_ok=True)
    _lancer_dry_run()
    plus_selectionnee = not _preview_contient_la_regle()

    return selectionnee and plus_selectionnee


def main() -> None:
    setup_logging()
    load_dotenv()

    base_url = f"http://localhost:{config.PORT}"

    logger.info("=== check_api_regles_acceptance : démarrage ===")
    progress_logger.info("=== check_api_regles_acceptance : démarrage ===")

    try:
        cases = load_cases(CASES_PATH)

        with httpx.Client() as client:
            evaluations = [evaluate_case(client, base_url, case) for case in cases]
            for evaluation in evaluations:
                statut = "OK" if evaluation["reussi"] else "ÉCHEC"
                progress_logger.info(
                    f"check_api_regles_acceptance — {evaluation['description']} "
                    f"({evaluation['detail']}) — {statut}"
                )

            boucle_ok = _verifier_boucle_revue(client, base_url)
            progress_logger.info(
                f"check_api_regles_acceptance — boucle de revue "
                f"(règle {NUMERO_REGLE_BOUCLE_REVUE}, annotée puis retirée) — "
                f"{'OK' if boucle_ok else 'ÉCHEC'}"
            )

    except Exception as e:
        logger.error("check_api_regles_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    if not (is_acceptable(evaluations) and boucle_ok):
        logger.error("check_api_regles_acceptance : au moins un cas a échoué")
        sys.exit(1)

    logger.info("=== check_api_regles_acceptance : succès ===")
    progress_logger.info("=== check_api_regles_acceptance : succès ===")


if __name__ == "__main__":
    main()
