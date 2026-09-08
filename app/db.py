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
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


def _build_url(nom_base: str) -> str:
    """URL de connexion à la base nommée, depuis les identifiants du .env."""
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{nom_base}"


def build_database_url_referentiel() -> str:
    """Base du référentiel Opquast (245 règles, vecteurs)."""
    return _build_url(os.environ["POSTGRES_DB"])


def build_database_url_audit() -> str:
    """Base du domaine audit."""
    return _build_url(os.environ["POSTGRES_DB_AUDIT"])


# Un moteur par base pour tout le processus : un pool recréé à chaque requête
# annulerait l'intérêt du pool. Aucune session « par défaut » n'est exposée —
# tout appelant doit dire quel domaine il interroge.
_engine_referentiel = create_engine(build_database_url_referentiel())
_SessionReferentiel = sessionmaker(bind=_engine_referentiel)


def get_session_referentiel() -> Iterator[Session]:
    """Dépendance FastAPI : une session référentiel par requête."""
    session = _SessionReferentiel()
    try:
        yield session
    finally:
        session.close()


def get_session_audit() -> Iterator[Session]:
    """Dépendance FastAPI : une session audit par requête.

    Le moteur est construit à l'appel et non au chargement du module : aucun
    service ne consomme encore ce domaine (app/api_audit reste à concevoir
    avec US1), inutile d'exiger POSTGRES_DB_AUDIT de tous les points d'entrée.
    """
    engine = create_engine(build_database_url_audit())
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
