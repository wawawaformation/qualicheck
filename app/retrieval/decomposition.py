"""
Client LLM pour la décomposition des questions multi-sujets.

Découpe une question utilisateur en 1..N sous-questions avant retrieval,
pour que chaque sujet distinct interroge pgvector séparément. Voir
docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md.
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

PROMPT_PATH = Path(__file__).parent / "prompts" / "decompose_question.md"


class DecompositionOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    sous_questions: list[str]


class DecompositionClient:
    """Client pour la décomposition LLM d'une question en sous-questions."""

    def __init__(self):
        """Initialise le client Azure OpenAI (rôle decomposition, timeout 2s)."""
        manifest = load_manifest()
        role = manifest["decomposition"]

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
            timeout=2,
        )
        self.parser = JsonOutputParser(pydantic_object=DecompositionOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def _charger_prompt(self, question: str) -> str:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            prompt_text = f.read()
        return prompt_text.replace("{question}", question)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str) -> list[str]:
        prompt = self._charger_prompt(question)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["sous_questions"]

    def decomposer(self, question: str) -> list[str]:
        """Découpe une question en sous-questions (1 élément si mono-sujet).

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        JSON malformé), avec backoff exponentiel (2s, 4s, 8s). Après 3
        échecs, fail-open : retombe sur [question] telle quelle plutôt que
        de faire échouer toute la réponse à l'utilisateur.
        """
        try:
            return self._appeler_llm(question)
        except Exception:
            logger.warning(
                f"decomposition : échec après 3 tentatives pour « {question} », "
                "fail-open (traitée comme mono-sujet)"
            )
            return [question]
