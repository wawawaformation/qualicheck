"""Point d'entrée CLI de l'agent US2 (increment A1a).

Pose une question en argument, affiche la réponse et les métriques du tour
(latence, tokens, nombre de tours) sur stdout. Boucle et outil dans
app/agent_us2/. Voir le schéma conception/3_autre_us/us2_question_libre/
increments/A_agent_nu/A1_boucle_et_premier_outil.drawio.

Nécessite l'API des règles démarrée (make api-regles) pour l'outil
recherche_regles.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent_us2.loop import repondre  # noqa: E402


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Agent US2 (question libre) — increment A1a, CLI"
    )
    parser.add_argument("question", help="Question posée à l'agent")
    args = parser.parse_args()

    try:
        resultat = repondre(args.question)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    print(resultat.reponse)
    print()
    print("--- métriques ---")
    print(f"tours          : {resultat.nb_tours}")
    print(f"durée          : {resultat.duree_s:.1f} s")
    print(f"tokens entrée  : {resultat.tokens_entree}")
    print(f"tokens sortie  : {resultat.tokens_sortie}")
    print(f"coût estimé    : {resultat.cout_euros_estime:.6f} € (tarif catalogue, non vérifié)")
    print(f"règles citées  : {resultat.regles_citees or 'aucune'}")


if __name__ == "__main__":
    main()
