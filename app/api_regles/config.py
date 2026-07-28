"""
Source de vérité de la configuration de l'API données.

Aucun autre module de app/api_regles/ ne lit d'environnement ni de YAML : une
valeur de configuration ne doit exister qu'à un seul endroit.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


def load_manifest() -> dict:
    """Charge la configuration courante de l'API (app/api_regles/manifest.yml)."""
    manifest_path = Path(__file__).parent / "manifest.yml"
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


_MANIFEST = load_manifest()

TITLE: str = _MANIFEST["api"]["title"]
DESCRIPTION: str = _MANIFEST["api"]["description"]
VERSION: str = _MANIFEST["api"]["version"]
PORT: int = _MANIFEST["api"]["port"]
CORS_ALLOWED_ORIGINS: list[str] = _MANIFEST["cors"]["allowed_origins"]
REVIEW_NOTE_MAX_LENGTH: int = _MANIFEST["validation"]["review_note_max_length"]

# Attribution CC BY-SA 4.0 : obligation de la licence du référentiel Opquast,
# que cette API distribue. Voir
# docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md
LICENCE_NOM: str = _MANIFEST["licence"]["nom"]
LICENCE_URL: str = _MANIFEST["licence"]["url"]
ATTRIBUTION: str = _MANIFEST["licence"]["attribution"]


CLIENTS: list[dict] = _MANIFEST.get("clients", [])


def clients_tokens() -> dict[str, str]:
    """
    {nom_client: jeton} pour chaque client déclaré dans le manifeste.

    Lève RuntimeError si un client déclaré n'a pas son jeton renseigné dans
    l'environnement : sans ce garde-fou, ce client serait silencieusement
    exclu de l'authentification plutôt que de faire échouer le démarrage.
    Lu à chaque appel plutôt que figé au chargement, pour rester testable.
    """
    jetons = {}
    for client in CLIENTS:
        valeur = os.getenv(client["env_var_token"], "")
        if not valeur:
            raise RuntimeError(
                f"{client['env_var_token']} absente ou vide dans .env : "
                f"le client « {client['nom']} » ne peut pas être authentifié."
            )
        jetons[client["nom"]] = valeur
    return jetons
