"""
Étape 3 — Enrichissement du pipeline d'ingestion.

Transformation de chaque Rule en EnrichedRule via appel LLM (Kimi K2.6).
"""

import logging

from .aggregation import EnrichedRules, Rules
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


def enrich_rules(rules: Rules) -> EnrichedRules:
    """
    Enrichit une collection de Rules via LLM.

    Chaque règle est enrichie avec strategie_analyse, strategie_justification,
    et guide_analyse générés par l'agent Kimi K2.6.

    Args:
        rules: Collection Rules validée (Étape 2)

    Returns:
        Collection EnrichedRules avec tous les champs enrichis

    Raises:
        ValueError: Si une règle échoue enrichissement (3 timeouts épuisés
            ou toute autre erreur d'enrichissement)
    """
    llm_client = LLMClient()
    enriched_list = []

    for rule in rules.regles:
        try:
            enriched = llm_client.enrich_single_rule(rule)
            enriched_list.append(enriched)
        except TimeoutError as e:
            logger.error(f"Règle {rule.number} — enrichissement : KO (3 timeouts)")
            raise ValueError(f"Enrichissement échoué pour règle {rule.number}") from e
        except Exception as e:
            logger.error(f"Règle {rule.number} — enrichissement : KO ({e})")
            raise

    enriched_rules = EnrichedRules(enriched_list)
    logger.info(f"Enrichissement : {len(enriched_list)} règles enrichies")
    return enriched_rules
