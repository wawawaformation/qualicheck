"""
Configuration de l'agent US2 (question libre) : app/agent_us2/config.yml.
"""

from pathlib import Path

import yaml
from dotenv import load_dotenv

# Chargé au niveau module (comme app/api_regles/config.py) : le serveur
# FastAPI (uvicorn app.agent_us2.main:app) n'a sinon aucun autre point
# d'entrée qui charge .env, contrairement à scripts/agent_cli.py qui
# appelle load_dotenv() lui-même. Sans ça, AZURE_MODEL_GPT_MINI etc.
# valent None en environnement réel — bug constaté au smoke test du
# 2026-09-19.
load_dotenv()


def load_config() -> dict:
    """Charge les décisions courantes de l'agent (app/agent_us2/config.yml)."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
