"""
Boucle de l'agent US2 (increment A1) : un appel LLM avec tool-calling natif,
décision d'appeler l'outil recherche_regles ou de répondre, exécution de
l'outil, retour au LLM. Voir le schéma
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/
A1_boucle_et_premier_outil.drawio.

"Messages du tour" ici = l'historique de CE seul appel (system/user, appels
outil, résultats outil, réponse finale), vidé après la réponse — à ne pas
confondre avec la mémoire de conversation entre questions (increments E1/E2,
bien plus tard).
"""

import json
import os
import time
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agent_us2.config import load_config
from app.agent_us2.tools import rechercher_regles
from app.observability.tracing import current_trace_id, get_tracer

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond à des questions de qualité web en "
    "t'appuyant uniquement sur les règles Opquast. Utilise l'outil "
    "rechercher_regles pour trouver les règles pertinentes avant de "
    "répondre. Cite le numéro de chaque règle que tu utilises dans ta "
    "réponse."
)


@dataclass
class ResultatAgent:
    """Réponse d'A1 et ses métriques (voir increments.md, mesure d'A1).

    Pas de taux d'erreur ici : c'est une statistique sur plusieurs
    questions, pas une seule réponse.
    cout_euros_estime est une ESTIMATION (voir app/agent_us2/config.yml,
    prix_entree_par_million/prix_sortie_par_million) : tarif catalogue,
    pas une facture Azure réelle vérifiée pour ce déploiement — même
    réserve que app/retrieval/config.yml pour le même modèle.
    """

    reponse: str
    regles_citees: list[dict]
    nb_tours: int
    duree_s: float
    tokens_entree: int
    tokens_sortie: int
    cout_euros_estime: float
    trace_id: str | None


def _construire_llm(config_llm: dict) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv(config_llm["env_var_endpoint"]),
        api_key=os.getenv(config_llm["env_var_api_key"]),
        model=os.getenv(config_llm["env_var_deployment"]),
        temperature=config_llm["temperature"],
        timeout=30,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    reraise=True,
)
def _appeler_llm(llm: ChatOpenAI, messages: list) -> AIMessage:
    return llm.invoke(messages)


def _estimer_cout_euros(config_llm: dict, tokens_entree: int, tokens_sortie: int) -> float:
    return (
        tokens_entree / 1_000_000 * config_llm["prix_entree_par_million"]
        + tokens_sortie / 1_000_000 * config_llm["prix_sortie_par_million"]
    )


def repondre(question: str) -> ResultatAgent:
    """Répond à une question autonome (pas de mémoire entre questions, A1)."""
    config = load_config()
    config_llm = config["llm"]
    max_tours = config["agent_a1"]["max_tours_securite"]
    tracer = get_tracer()

    llm = _construire_llm(config_llm).bind_tools([rechercher_regles])
    messages: list = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    with tracer.start_as_current_span("repondre"):
        trace_id = current_trace_id()
        debut = time.monotonic()
        tokens_entree = tokens_sortie = 0
        regles_citees: dict[int, str] = {}
        ai_message: AIMessage | None = None

        for tour in range(1, max_tours + 1):
            with tracer.start_as_current_span("appel_llm", attributes={"tour": tour}) as span:
                ai_message = _appeler_llm(llm, messages)
                usage = ai_message.usage_metadata or {}
                span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
                span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))

            messages.append(ai_message)
            tokens_entree += usage.get("input_tokens", 0)
            tokens_sortie += usage.get("output_tokens", 0)

            if not ai_message.tool_calls:
                break

            for appel in ai_message.tool_calls:
                with tracer.start_as_current_span(
                    "appel_outil", attributes={"outil": "rechercher_regles"}
                ) as span:
                    resultat_texte = rechercher_regles.invoke(appel["args"])
                messages.append(ToolMessage(content=resultat_texte, tool_call_id=appel["id"]))
                try:
                    for r in json.loads(resultat_texte)["resultats"]:
                        regles_citees[r["numero"]] = r["intitule"]
                except (json.JSONDecodeError, KeyError):
                    pass
        else:
            return ResultatAgent(
                reponse=(
                    f"L'agent n'a pas conclu en {max_tours} tours (filet de "
                    "sécurité technique, pas encore le seuil C1)."
                ),
                regles_citees=_trier_regles_citees(regles_citees),
                nb_tours=max_tours,
                duree_s=time.monotonic() - debut,
                tokens_entree=tokens_entree,
                tokens_sortie=tokens_sortie,
                cout_euros_estime=_estimer_cout_euros(config_llm, tokens_entree, tokens_sortie),
                trace_id=trace_id,
            )

        return ResultatAgent(
            reponse=ai_message.content,
            regles_citees=_trier_regles_citees(regles_citees),
            nb_tours=tour,
            duree_s=time.monotonic() - debut,
            tokens_entree=tokens_entree,
            tokens_sortie=tokens_sortie,
            cout_euros_estime=_estimer_cout_euros(config_llm, tokens_entree, tokens_sortie),
            trace_id=trace_id,
        )


def _trier_regles_citees(regles_citees: dict[int, str]) -> list[dict]:
    return [
        {"numero": numero, "intitule": regles_citees[numero]}
        for numero in sorted(regles_citees)
    ]
