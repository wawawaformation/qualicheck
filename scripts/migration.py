"""Point d'entrée pour appliquer les migrations Alembic.

Lance `alembic upgrade head` depuis app/migration/ via subprocess.
Retourne le code de sortie d'Alembic (0 = succès, non-nul = erreur).
"""
import subprocess
import sys
from pathlib import Path

# Répertoire contenant alembic.ini
MIGRATION_DIR = Path(__file__).resolve().parents[1] / "app" / "migration"


def main() -> None:
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=MIGRATION_DIR,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
