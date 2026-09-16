"""
Configuration du retrieval (US2 question libre) : app/retrieval/config.yml.
"""

from pathlib import Path

import yaml


def load_config() -> dict:
    """Charge les décisions courantes du retrieval (app/retrieval/config.yml)."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
