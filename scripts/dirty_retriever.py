"""Point d'entrée pour interroger les règles Opquast par similarité sémantique.

Outil de veille ad hoc : prend une question en argument, calcule son
embedding réel (coût Azure à chaque exécution) et affiche en JSON les 3
règles les plus proches (similarité cosinus pgvector).
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.dirty_retriever import query_top_n_regles  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402

TOP_N = 3


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Question en langage naturel")
    args = parser.parse_args()

    vector = EmbeddingClient().embed_batch([args.question])[0]

    with Session(get_engine()) as session:
        resultats = query_top_n_regles(session, vector, TOP_N)

    print(json.dumps(resultats, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
