"""
Client LangChain pour enrichissement LLM via Azure Kimi K2.6.

Gère l'intégration Azure OpenAI, le parsing JSON et la retry logic.
"""

import logging
import os
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from .schema import EnrichedRule
from .schema import RuleAggregation as Rule

logger = logging.getLogger(__name__)

PROMPT_PLACEHOLDERS = [
    "intitule",
    "contexte",
    "solution",
    "controle",
    "objectifs",
    "tags",
    "phases",
]


class EnrichmentOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    strategie_analyse: str
    strategie_justification: str
    guide_analyse: str


class LLMClient:
    """Client pour enrichissement LLM de règles."""

    def __init__(self):
        """Initialise le client Azure OpenAI et le parser JSON."""
        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv("AZURE_DEPLOYMENT_INGESTION"),
        )
        self.parser = JsonOutputParser(pydantic_object=EnrichmentOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def load_prompt(self, rule: Rule) -> str:
        """
        Charge le prompt depuis prompts/enrich_rule.md et remplace les placeholders.

        Remplacement manuel (pas de str.format()) car le prompt contient des
        accolades JSON littérales dans les exemples few-shot, qui entreraient
        en conflit avec la syntaxe de formatage de PromptTemplate.
        """
        prompt_path = Path(__file__).parent / "prompts" / "enrich_rule.md"
        with open(prompt_path, encoding="utf-8") as f:
            prompt_text = f.read()

        values = {
            "intitule": rule.intitule,
            "contexte": rule.contexte or "(non disponible)",
            "solution": rule.solution,
            "controle": rule.controle,
            "objectifs": ", ".join(rule.objectifs),
            "tags": ", ".join(rule.tags),
            "phases": ", ".join(rule.phases),
        }
        for placeholder in PROMPT_PLACEHOLDERS:
            prompt_text = prompt_text.replace(f"{{{placeholder}}}", values[placeholder])

        return prompt_text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def enrich_single_rule(self, rule: Rule) -> EnrichedRule:
        """
        Enrichit une règle via LLM avec retry logic.

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        autre), avec backoff exponentiel (2s, 4s, 8s).

        Args:
            rule: Rule à enrichir

        Returns:
            EnrichedRule avec champs d'enrichissement

        Raises:
            TimeoutError: Si les 3 tentatives échouent (dernière exception relevée)

        Note:
            Seule la tentative réussie est comptabilisée dans les totaux de
            tokens — les tentatives échouées avant succès ne remontent pas
            de usage_metadata exploitable.
        """
        formatted_prompt = self.load_prompt(rule)

        response = self.llm.invoke(formatted_prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
            theme=rule.theme,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=rule.objectifs,
            tags=rule.tags,
            phases=rule.phases,
            slug=rule.slug,
            strategie_analyse=parsed["strategie_analyse"],
            strategie_justification=parsed["strategie_justification"],
            guide_analyse=parsed["guide_analyse"],
            strategie_source="ia_import",
            llm_provider="kimi-k2.6",
        )
