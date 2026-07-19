"""
Étape 2 — Agrégation du pipeline d'ingestion.

Fusion de données acquises (API + scraping) en objets Rule validés,
puis composition d'une collection Rules complètement validée.
"""

import logging

from .schema import EnrichedRule, RuleAggregation

logger = logging.getLogger(__name__)

Rule = RuleAggregation


class Rules:
    """Collection de règles complètement validées (non-vide)."""

    def __init__(self, rules_list: list[Rule]):
        if not rules_list:
            raise ValueError("Collection de règles ne peut pas être vide")
        self.rules = rules_list

    @property
    def regles(self):
        """Rétrocompatibilité : alias français pour accès à la liste."""
        return self.rules


def aggregate_rules(acquired_rules: list[dict]) -> Rules:
    """
    Agrège des règles acquises (dicts API + scraping) en collection Rules validée.

    Args:
        acquired_rules: Sortie de acquisition.acquire_rules() — liste de dicts

    Returns:
        Collection Rules entièrement validée

    Raises:
        ValueError: Si une règle est incomplète ou invalide
        KeyError: Si un champ attendu manque
    """
    validated_rules = []
    for rule_data in acquired_rules:
        try:
            rule = Rule(**rule_data)
            validated_rules.append(rule)
        except Exception as e:
            rule_id = rule_data.get("id", "unknown")
            logger.error(
                f"Règle {rule_id} — agrégation : KO ({str(e)})"
            )
            raise ValueError(f"Règle {rule_id} invalide: {e}") from e

    rules = Rules(validated_rules)
    logger.info(f"Agrégation : {len(validated_rules)} règles validées")
    return rules


class EnrichedRules:
    """Collection de règles complètement enrichies (non-vide)."""

    def __init__(self, enriched_rules: list[EnrichedRule]):
        if not enriched_rules:
            raise ValueError("Collection de règles enrichies ne peut pas être vide")
        self.enriched_rules = enriched_rules
        self.input_tokens = 0
        self.output_tokens = 0

    @property
    def regles(self):
        """Rétrocompatibilité : alias français pour accès à la liste."""
        return self.enriched_rules