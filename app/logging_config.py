"""
Configuration centralisée du logging pour QualiCheck.

Permet de configurer les handlers fichier et console une seule fois,
réutilisable par tous les scripts et modules.
"""

import logging
import os
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file="logs/ingestion.log"):
    """
    Configure le logging avec handler fichier uniquement (pas de console).

    Args:
        log_level: Niveau de log (default: INFO)
        log_file: Chemin du fichier de log (default: logs/ingestion.log)
    """
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
