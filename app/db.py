"""
Accès PostgreSQL de l'étage données.

Partagé entre le pipeline d'ingestion et l'API. Lit les identifiants de
connexion depuis .env : ce sont des secrets, pas de la configuration d'API —
app/api_regles/config.py ne les connaît pas.
"""

import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


def build_database_url() -> str:
    """URL de connexion à la base de développement (POSTGRES_DB)."""
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.environ["POSTGRES_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def build_engine() -> Engine:
    """Moteur SQLAlchemy. create_engine n'ouvre aucune connexion ici."""
    return create_engine(build_database_url())


# Un seul moteur pour tout le processus : un pool recréé à chaque requête
# annulerait l'intérêt du pool.
_engine = build_engine()
_SessionLocal = sessionmaker(bind=_engine)


def get_session() -> Iterator[Session]:
    """
    Dépendance FastAPI : une session par requête, fermée à la fin même en cas
    d'exception.
    """
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
