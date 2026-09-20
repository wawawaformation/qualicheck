"""Vide les tables du référentiel Opquast (theme, regle, objectif, phase, tag
et leurs tables d'association), sans toucher au cœur métier QualiCheck
(utilisateur, audit, page, constat).

Utile pour retester une ingestion sans redescendre/remonter toute la
migration Alembic.

Destructif : le TRUNCATE vise POSTGRES_DB (la vraie base de dev) et la
régénération des règles coûte un appel LLM chacune. Le script annonce donc le
nombre de règles et la base visée, et n'agit qu'après un « y » explicite (même
convention que scripts/ingestion.py).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.stockage import clear_opquast_tables  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.models.referentiel import Regle  # noqa: E402


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def confirmer(nb_regles: int, base: str) -> bool:
    """
    Demande confirmation avant de vider le référentiel. Seul « y » confirme :
    Entrée, « oui » ou une entrée standard fermée (pipe, cron) refusent.
    """
    try:
        reponse = input(
            f"Cela va supprimer les {nb_regles} règle(s) de la base « {base} ». Confirmer ? [y/N] "
        )
    except EOFError:
        return False
    return reponse.strip().lower() == "y"


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    with Session(engine) as session:
        if not confirmer(session.query(Regle).count(), os.environ["POSTGRES_DB"]):
            print("Suppression annulée.")
            return
        clear_opquast_tables(session)


if __name__ == "__main__":
    main()
