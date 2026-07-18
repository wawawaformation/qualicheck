"""
Étape 1 — Acquisition du pipeline d'ingestion.

Récupère les 245 règles Opquast via l'API REST publique,
puis complète les champs manquants par scraping du site Opquast.

Détail : conception/2_ingestion/ingestion.md
"""

import logging
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from ..logging_config import setup_logging
from .schema import RuleAcquisition

logger = logging.getLogger(__name__)


def build_rule_url(slug: str) -> str:
    """
    Construit l'URL de scraping pour une règle Opquast.

    Args:
        slug: Slug de la règle (ex. "regle-avec-des-tirets")

    Returns:
        URL complète de la règle sur le site Opquast
    """
    base_url = os.getenv("OPQUAST_SITE_BASE_URL")
    return f"{base_url}{slug}"


def fetch_api() -> list[dict]:
    """
    Récupère la liste des règles Opquast via l'API REST publique.

    Returns:
        Liste de dictionnaires représentant les règles Opquast
    """
    load_dotenv()
    url = os.getenv("OPQUAST_API_BASE_URL")
    if not url:
        raise ValueError("OPQUAST_API_BASE_URL not set in environment")

    logger.info("Fetching rules from API: %s", url)
    response = requests.get(url)
    response.raise_for_status()

    rules_data = response.json()
    logger.info("Retrieved %d rules from API", len(rules_data))
    rules = []

    for rule in rules_data:
        rule_acquisition = RuleAcquisition(
            id=rule["id"],
            number=rule["number"],
            intitule=rule["description"]["fr"],
            objectifs=rule["goal"]["fr"],
            tags=rule["metadata"]["Tags"],
            phases=rule["metadata"]["Phases projet"],
            slug=rule["slug"]["fr"],
        )
        rules.append(rule_acquisition.model_dump())

    logger.info("Successfully parsed %d rules", len(rules))
    return rules


def scrape_rule(slug: str) -> dict[str, str]:
    """
    Scrape les informations d'une règle Opquast depuis le site web pour extraire les champs
    `solution` et `controle`.

    Args:
        slug: Slug de la règle

    Returns:
        Dictionnaire contenant "solution" et "controle"
    """
    
    logger.info("Scraping rule: %s", slug)

    url = build_rule_url(slug)
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    solution = ""
    controle = ""

    headings = soup.find_all(["h2", "h3"])
    for heading in headings:
        heading_text = heading.get_text(strip=True).lower()

        if "solution" in heading_text:
            next_p = heading.find_next("p")
            if next_p:
                solution = next_p.get_text(strip=True)
                logger.debug("Found solution for slug: %s", slug)

        if "contrôle" in heading_text or "controle" in heading_text:
            next_p = heading.find_next("p")
            if next_p:
                controle = next_p.get_text(strip=True)
                logger.debug("Found controle for slug: %s", slug)

    if not solution or not controle:
        logger.error("Solution or Controle not found for slug: %s", slug)
        raise ValueError(f"Solution or Controle not found for slug: {slug}")

    logger.info("Successfully scraped rule: %s", slug)
    return {
        "solution": solution,
        "controle": controle,
    }



def acquire_rules() -> list[dict]:
    """
    Acquiert les règles Opquast via l'API et complète les champs manquants par scraping.

    Returns:
        Liste de dictionnaires représentant les règles Opquast avec tous les champs remplis
    """
    
    
    rules = fetch_api()
    
    for rule in rules:
        scraped_data = scrape_rule(rule["slug"])
        rule.update(scraped_data)
    return rules

if __name__ == "__main__":
    setup_logging()
    rules = acquire_rules()
    for rule in rules:
        print(rule)