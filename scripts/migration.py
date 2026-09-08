"""Point d'entrée pour appliquer les migrations Alembic.

Deux domaines, deux chaînes, deux bases (scission du 2026-09-08) :
    python scripts/migration.py             -> référentiel (défaut)
    python scripts/migration.py audit       -> domaine audit

Lance `alembic upgrade head` depuis le dossier de la chaîne visée et retourne
le code de sortie d'Alembic (0 = succès, non-nul = erreur).
"""
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "app"

# Nom du domaine -> dossier contenant son alembic.ini
CHAINES = {
    "referentiel": RACINE / "migration",
    "audit": RACINE / "migration_audit",
}


def main() -> None:
    domaine = sys.argv[1] if len(sys.argv) > 1 else "referentiel"
    if domaine not in CHAINES:
        attendus = ", ".join(sorted(CHAINES))
        print(f"Domaine inconnu : {domaine!r}. Attendu : {attendus}.")
        sys.exit(2)

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=CHAINES[domaine],
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
