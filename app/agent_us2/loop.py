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
from opentelemetry.trace import Status, StatusCode
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agent_us2.config import load_config
from app.agent_us2.tools import lire_regle, rechercher_regles
from app.observability.tracing import (
    current_trace_id,
    get_tracer,
    set_llm_span_io,
    set_tool_span_io,
)

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond à des questions de qualité web en "
    "t'appuyant uniquement sur les règles Opquast. Utilise l'outil "
    "rechercher_regles pour trouver les règles pertinentes avant de "
    "répondre. Utilise l'outil lire_regle quand l'utilisateur cite un "
    "numéro de règle, ou pour lire en entier une règle dont la recherche a "
    "indiqué solution_tronquee. Cite le numéro de chaque règle que tu "
    "utilises dans ta réponse."
)

# Table d'aiguillage nom -> outil : l'appel d'un outil la consulte à chaque fois.
OUTILS = {
    rechercher_regles.name: rechercher_regles,
    lire_regle.name: lire_regle,
}


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
    # Vrai dès qu'un outil a renvoyé un statut >= 500 pendant la question,
    # même si un appel suivant a réussi (c'est l'API qui décide du statut final).
    panne_outil: bool = False


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

    llm = _construire_llm(config_llm).bind_tools(list(OUTILS.values()))
    messages: list = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    with tracer.start_as_current_span("questions_libres"):
        trace_id = current_trace_id()
        debut = time.monotonic()
        tokens_entree = tokens_sortie = 0
        regles_citees: dict[int, str] = {}
        panne_outil = False
        ai_message: AIMessage | None = None

        for tour in range(1, max_tours + 1):
            with tracer.start_as_current_span(
                "questions_libres.appel_llm", attributes={"tour": tour}
            ) as span:
                ai_message = _appeler_llm(llm, messages)
                set_llm_span_io(span, messages, ai_message, config_llm=config_llm)
                usage = ai_message.usage_metadata or {}
                span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
                span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))

            messages.append(ai_message)
            tokens_entree += usage.get("input_tokens", 0)
            tokens_sortie += usage.get("output_tokens", 0)

            if not ai_message.tool_calls:
                break

            for appel in ai_message.tool_calls:
                outil = OUTILS.get(appel["name"])
                # Un nom inventé par le LLM ne devient pas un nom de span (ils
                # proliféreraient dans Langfuse) : il reste visible en attribut.
                nom_span = appel["name"] if outil else "inconnu"
                with tracer.start_as_current_span(
                    f"questions_libres.appel_outil.{nom_span}",
                    attributes={"outil": appel["name"]},
                ) as span:
                    if outil is None:
                        # Même contrat que les outils : un résultat lisible par
                        # l'agent, pas une exception.
                        resultat_texte = json.dumps(
                            {"statut": 404, "erreur": f"Outil inconnu : {appel['name']}"},
                            ensure_ascii=False,
                        )
                    else:
                        resultat_texte = outil.invoke(appel["args"])
                    set_tool_span_io(span, appel["args"], resultat_texte)
                    try:
                        resultat = json.loads(resultat_texte)
                    except (json.JSONDecodeError, TypeError):
                        resultat = None
                    # Un résultat d'erreur est un dict avec un "statut" entier.
                    # Seul un 5xx est une panne ; un 404 (règle inconnue) est
                    # un résultat normal.
                    if isinstance(resultat, dict) and isinstance(resultat.get("statut"), int):
                        span.set_attribute("outil.statut", resultat["statut"])
                        if resultat["statut"] >= 500:
                            message = str(resultat.get("erreur", ""))
                            span.set_status(Status(StatusCode.ERROR, message))
                            panne_outil = True
                messages.append(ToolMessage(content=resultat_texte, tool_call_id=appel["id"]))
                _noter_regles_citees(resultat, regles_citees)
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
                panne_outil=panne_outil,
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
            panne_outil=panne_outil,
        )


def _trier_regles_citees(regles_citees: dict[int, str]) -> list[dict]:
    return [
        {"numero": numero, "intitule": regles_citees[numero]}
        for numero in sorted(regles_citees)
    ]


def _noter_regles_citees(resultat: object, regles_citees: dict[int, str]) -> None:
    """Ajoute les règles d'un résultat d'outil : liste "resultats" (recherche)
    ou règle seule (lire_regle). Un résultat d'erreur ou illisible ne cite rien."""
    if not isinstance(resultat, dict):
        return
    try:
        if "resultats" in resultat:
            for r in resultat["resultats"]:
                regles_citees[r["numero"]] = r["intitule"]
        else:
            regles_citees[resultat["numero"]] = resultat["intitule"]
    except KeyError:
        pass
