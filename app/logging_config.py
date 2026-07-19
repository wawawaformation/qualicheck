"""
Configuration centralisée du logging pour QualiCheck.

Permet de configurer les handlers fichier et console une seule fois,
réutilisable par tous les scripts et modules.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file="logs/ingestion.log"):
    """
    Configure le logging : fichier complet (tous les modules, niveau
    log_level) + console pour les erreurs bloquantes (WARNING+) et la
    progression (logger "progress", niveau INFO).

    Args:
        log_level: Niveau de log du fichier (default: INFO)
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

    # -- Console : erreurs bloquantes (WARNING+), tous modules confondus ----
    error_console_handler = logging.StreamHandler(sys.stderr)
    error_console_handler.setLevel(logging.WARNING)
    error_console_handler.setFormatter(formatter)
    root_logger.addHandler(error_console_handler)

    # -- Console : progression (logger "progress" dédié, niveau INFO) -------
    progress_console_handler = logging.StreamHandler(sys.stdout)
    progress_console_handler.setLevel(logging.INFO)
    progress_console_handler.setFormatter(formatter)

    progress_logger = logging.getLogger("progress")
    progress_logger.setLevel(logging.INFO)
    progress_logger.addHandler(progress_console_handler)
    progress_logger.propagate = False
