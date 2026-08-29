"""
Étape 1 — Acquisition du pipeline d'ingestion.

Récupère les 245 règles Opquast via l'API REST publique,
puis complète les champs manquants par scraping du site Opquast.

Détail : conception/2_us0/ingestion/ingestion.md
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
            theme=rule["metadata"]["Thématiques"][0],
            objectifs=rule["goal"]["fr"],
            tags=rule["metadata"]["Tags"],
            phases=rule["metadata"]["Phases projet"],
            slug=rule["slug"]["fr"],
        )
        rules.append(rule_acquisition.model_dump())

    logger.info("Successfully parsed %d rules", len(rules))
    return rules


def extract_content_after(heading) -> str:
    """
    Collecte le contenu (texte) des frères d'un heading jusqu'au <h2> suivant.

    Chaque <ul> devient un bloc où chaque <li> est rendu sur sa propre ligne
    préfixée par "- ". Tout autre frère non vide (<p>, <div>, ou nœud texte
    direct — variantes observées sur des règles Opquast réelles, ex. règle 14
    pour le texte direct et règle 27 pour le <div>) est traité comme un
    simple bloc de texte. Les blocs sont joints par un saut de ligne.

    Args:
        heading: Élément BeautifulSoup <h2> de départ

    Returns:
        Texte extrait (chaîne vide si aucun contenu trouvé)
    """
    blocks = []
    for sibling in heading.next_siblings:
        if getattr(sibling, "name", None) == "h2":
            break
        if sibling.name == "ul":
            items = [li.get_text(strip=True) for li in sibling.find_all("li")]
            if items:
                blocks.append("\n".join(f"- {item}" for item in items))
        else:
            text = sibling.get_text(strip=True)
            if text:
                blocks.append(text)

    return "\n".join(blocks)


def scrape_rule(slug: str) -> dict[str, str | None]:
    """
    Scrape les informations d'une règle Opquast depuis le site web pour extraire
    les champs `solution`, `controle` et `contexte`.

    L'extraction est bornée au conteneur `div.c-rule-content` : le pied de page
    du site est structurellement hors de ce conteneur et ne peut donc jamais
    être capturé par erreur.

    Args:
        slug: Slug de la règle

    Returns:
        Dictionnaire contenant "solution", "controle" (str) et "contexte" (str | None)

    Raises:
        ValueError: Si le conteneur de contenu est introuvable, ou si
            solution/controle sont vides après extraction
    """
    logger.info("Scraping rule: %s", slug)

    url = build_rule_url(slug)
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.find("div", class_="c-rule-content")
    if content is None:
        logger.error("c-rule-content container not found for slug: %s", slug)
        raise ValueError(f"c-rule-content container not found for slug: {slug}")

    subtitle = soup.find(class_="c-rule-hero__subtitle")
    contexte = subtitle.get_text(strip=True) if subtitle else None

    solution = ""
    controle = ""

    for heading in content.find_all("h2"):
        heading_classes = heading.get("class") or []

        if "c-emoji-tools" in heading_classes:
            solution = extract_content_after(heading)
            logger.debug("Found solution for slug: %s", slug)

        if "c-emoji-check" in heading_classes:
            controle = extract_content_after(heading)
            logger.debug("Found controle for slug: %s", slug)

    if not solution or not controle:
        logger.error("Solution or Controle not found for slug: %s", slug)
        raise ValueError(f"Solution or Controle not found for slug: {slug}")

    logger.info("Successfully scraped rule: %s", slug)
    return {
        "solution": solution,
        "controle": controle,
        "contexte": contexte,
    }



def acquire_rules(limit: int | None = None) -> list[dict]:
    """
    Acquiert les règles Opquast via l'API et complète les champs manquants par scraping.

    Args:
        limit: Si renseigné, ne traite que les `limit` premières règles
            retournées par l'API (utile pour tester sans scraper/enrichir
            les 245 règles). None = toutes les règles.

    Returns:
        Liste de dictionnaires représentant les règles Opquast avec tous les champs remplis
    """
    rules = fetch_api()

    if limit is not None:
        rules = rules[:limit]

    for rule in rules:
        scraped_data = scrape_rule(rule["slug"])
        rule.update(scraped_data)
    return rules

if __name__ == "__main__":
    setup_logging()
    rules = acquire_rules()
    for rule in rules:
        print(rule)