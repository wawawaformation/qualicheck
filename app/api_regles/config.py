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


def admin_token() -> str:
    """
    Token Bearer attendu pour les écritures.

    Lève RuntimeError si le secret est absent ou vide : sans ce garde-fou, la
    clé attendue serait la chaîne vide et le PATCH deviendrait ouvert à tous.
    Lu à chaque appel plutôt que figé au chargement, pour rester testable.
    """
    token = os.getenv("FASTAPI_API_KEY", "")
    if not token:
        raise RuntimeError(
            "FASTAPI_API_KEY absente ou vide dans .env : l'API refuse de démarrer."
        )
    return token
