"""
Client LLM expérimental pour classer une question dans/hors périmètre
Opquast, SANS voir de candidats retrieval — teste l'hypothèse que le
biais de sélection mesuré sur JugementClient (le LLM peine à dire « non »
face à une liste de candidats déjà présentés comme plausibles) disparaît
quand il n'y a aucun candidat à sélectionner, juste la question elle-même
à classer. Voir docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.

Pas encore intégré à un pipeline de production — mesuré isolément par
scripts/mesure_guardrail_perimetre.py avant toute décision de construire.
"""

import logging
import os
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ingestion.llm_client import load_manifest

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "guardrail_perimetre.md"


class GuardrailOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    dans_perimetre: bool


class GuardrailClient:
    """Client pour la classification LLM dans/hors périmètre Opquast."""

    def __init__(self):
        """Initialise le client Azure OpenAI (rôle guardrail, timeout 2s)."""
        manifest = load_manifest()
        role = manifest["guardrail"]

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
            timeout=2,
        )
        self.parser = JsonOutputParser(pydantic_object=GuardrailOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def _construire_prompt(self, question: str) -> str:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            prompt_text = f.read()
        return prompt_text.replace("{question}", question)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str) -> bool:
        prompt = self._construire_prompt(question)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["dans_perimetre"]

    def est_dans_le_perimetre(self, question: str) -> bool:
        """Classe une question dans (True) ou hors (False) périmètre
        Opquast, sans voir de candidats retrieval. Retente automatiquement
        jusqu'à 3 fois en cas d'erreur, avec backoff exponentiel (2s, 4s,
        8s). Après 3 échecs, fail-open : considère la question dans le
        périmètre plutôt que de refuser par accident technique.
        """
        try:
            return self._appeler_llm(question)
        except Exception:
            logger.warning(
                f"guardrail : échec après 3 tentatives pour « {question} », "
                "fail-open (considérée dans le périmètre)"
            )
            return True
