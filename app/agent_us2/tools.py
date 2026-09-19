"""
Outil recherche_regles de l'agent US2 (increment A1) : recherche par
mots-clés dans l'API des règles (GET /regles?q=, accès libre, sans jeton —
voir conception/3_autre_us/us2_question_libre/increments/increments.md).

Le contrôle de citations (B1, vérifier que les règles citées existent
réellement) n'existe pas encore : ce module se contente de retourner ce
que l'API renvoie.
"""

import json
import os

import httpx
from langchain_core.tools import tool

from app.agent_us2.config import load_config

# GET /regles?q= n'est pas paginé et peut renvoyer beaucoup de règles sur un
# terme courant — un tool result trop volumineux gonflerait le coût et le
# contexte du LLM pour peu de gain.
MAX_RESULTATS = 10
LONGUEUR_MAX_SOLUTION = 300


def _base_url() -> str:
    """
    L'URL réelle vient de .env, pas de config.yml : elle diffère par
    environnement (dev/staging/prod), un fichier versionné ne convient
    pas. config.yml ne porte que le NOM de la variable à lire (même
    indirection que app/agent_us2/loop.py::_construire_llm).
    """
    return os.getenv(load_config()["api_regles"]["env_var_url"])


@tool
def rechercher_regles(mots_cles: str) -> str:
    """Recherche des règles Opquast par mots-clés.

    Utilise cet outil pour trouver les règles Opquast pertinentes avant de
    répondre à une question de qualité web.
    """
    reponse = httpx.get(f"{_base_url()}/regles", params={"q": mots_cles}, timeout=10)
    reponse.raise_for_status()
    regles = reponse.json()

    resultats = [
        {
            "numero": r["numero"],
            "intitule": r["intitule"],
            "solution": r["solution"][:LONGUEUR_MAX_SOLUTION],
        }
        for r in regles[:MAX_RESULTATS]
    ]
    return json.dumps(
        {"resultats": resultats, "total_trouve": len(regles)}, ensure_ascii=False
    )
