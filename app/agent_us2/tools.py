"""
Outils de l'agent US2 : rechercher_regles (increment A1) et lire_regle (A4),
appelés sur l'API des règles (accès libre, sans jeton — voir
conception/3_autre_us/us2_question_libre/increments/increments.md).

- rechercher_regles : recherche par mots-clés (GET /regles?q=), solutions
  abrégées (marqueur solution_tronquee).
- lire_regle : règle complète par son numéro (GET /regles/{numero}).

Contrat de résilience commun (A4) : aucune exception ne remonte vers
l'agent. Une panne devient un résultat {"statut": <code>, "erreur": <message>}
que le LLM peut lire et expliquer à l'utilisateur ; l'API injoignable (délai
dépassé, connexion impossible) est rapportée avec le statut 503.

Le contrôle de citations (B1, vérifier que les règles citées existent
réellement) n'existe pas encore : ce module se contente de retourner ce
que l'API renvoie.
"""

import json
import logging
import os

import httpx
from langchain_core.tools import tool

from app.agent_us2.config import load_config

logger = logging.getLogger(__name__)

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


def _appeler_api(chemin: str, params: dict | None = None) -> tuple[object, dict | None]:
    """
    GET sur l'API des règles. Retourne (données JSON, None) en cas de succès,
    ou (None, {"statut", "erreur"}) en cas d'échec : jamais d'exception.
    """
    try:
        reponse = httpx.get(f"{_base_url()}{chemin}", params=params, timeout=10)
        reponse.raise_for_status()
        return reponse.json(), None
    except httpx.HTTPStatusError as e:
        statut = e.response.status_code
        # Message de l'API (champ "detail") s'il existe ; sinon repli — un
        # proxy peut répondre en HTML, ou "detail" peut ne pas être un texte.
        try:
            detail = e.response.json()["detail"]
        except (ValueError, KeyError, TypeError):
            detail = None
        if not isinstance(detail, str) or not detail:
            detail = f"Erreur HTTP {statut}"
        logger.warning("API des règles : statut %s sur %s", statut, chemin)
        return None, {"statut": statut, "erreur": detail}
    except httpx.TransportError:
        # Délai dépassé ou connexion impossible : l'API ne répond pas.
        logger.warning("API des règles injoignable sur %s", chemin)
        return None, {"statut": 503, "erreur": "API des règles injoignable"}
    except ValueError:
        # Réponse 200 dont le corps n'est pas du JSON (proxy, page d'erreur) :
        # mauvaise réponse d'un service amont, donc 502.
        logger.warning("API des règles : réponse illisible sur %s", chemin)
        return None, {"statut": 502, "erreur": "Réponse illisible de l'API des règles"}


@tool
def rechercher_regles(mots_cles: str) -> str:
    """Recherche des règles Opquast par mots-clés.

    Utilise cet outil pour trouver les règles Opquast pertinentes avant de
    répondre à une question de qualité web. Les solutions sont abrégées
    quand solution_tronquee est vrai : appelle alors lire_regle pour
    obtenir le texte complet.
    """
    regles, erreur = _appeler_api("/regles", params={"q": mots_cles})
    if erreur:
        return json.dumps(erreur, ensure_ascii=False)

    resultats = [
        {
            "numero": r["numero"],
            "intitule": r["intitule"],
            "solution": r["solution"][:LONGUEUR_MAX_SOLUTION],
            "solution_tronquee": len(r["solution"]) > LONGUEUR_MAX_SOLUTION,
        }
        for r in regles[:MAX_RESULTATS]
    ]
    return json.dumps(
        {"resultats": resultats, "total_trouve": len(regles)}, ensure_ascii=False
    )


@tool
def lire_regle(numero: int) -> str:
    """Lit une règle Opquast complète à partir de son numéro.

    Utilise cet outil quand l'utilisateur cite un numéro de règle, ou pour
    lire en entier une règle dont la recherche a indiqué solution_tronquee
    à vrai.
    """
    regle, erreur = _appeler_api(f"/regles/{numero}")
    return json.dumps(erreur or regle, ensure_ascii=False)
