"""
Client LLM pour le jugement de pertinence des candidats retrouvés par le
retrieval (Temps 2 du mécanisme de refus). Voir
docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
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

PROMPT_PATH = Path(__file__).parent / "prompts" / "juger_pertinence.md"


class JugementOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    numeros_pertinents: list[int]


class JugementClient:
    """Client pour le jugement LLM de pertinence des candidats retrouvés."""

    def __init__(self):
        """Initialise le client Azure OpenAI (rôle jugement, timeout 2s)."""
        manifest = load_manifest()
        role = manifest["jugement"]

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
            timeout=2,
        )
        self.parser = JsonOutputParser(pydantic_object=JugementOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def _construire_prompt(self, question: str, candidats: list[tuple[int, str]]) -> str:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            prompt_text = f.read()
        candidats_texte = "\n\n".join(
            f"### Règle {numero}\n{texte}" for numero, texte in candidats
        )
        prompt_text = prompt_text.replace("{question}", question)
        prompt_text = prompt_text.replace("{candidats}", candidats_texte)
        return prompt_text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str, candidats: list[tuple[int, str]]) -> list[int]:
        prompt = self._construire_prompt(question, candidats)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["numeros_pertinents"]

    def juger(self, question: str, candidats: list[tuple[int, str]]) -> list[int]:
        """Juge lesquels des candidats répondent vraiment à la question.

        Retourne les numéros jugés pertinents (liste vide si aucun). Un
        numéro halluciné par le LLM hors du pool de candidats fournis
        est filtré silencieusement. Retente automatiquement jusqu'à 3
        fois en cas d'erreur, avec backoff exponentiel (2s, 4s, 8s).
        Après 3 échecs, fail-open : retourne tous les candidats non
        filtrés plutôt que de refuser par accident technique.
        """
        numeros_valides = {numero for numero, _ in candidats}
        try:
            numeros_juges = self._appeler_llm(question, candidats)
            return [n for n in numeros_juges if n in numeros_valides]
        except Exception:
            logger.warning(
                f"jugement : échec après 3 tentatives pour « {question} », "
                "fail-open (candidats non filtrés)"
            )
            return [numero for numero, _ in candidats]
