import os
import sys
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# -- Résolution des chemins --------------------------------------------------
# env.py est exécuté par Alembic depuis app/migration_audit/.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# -- Chargement du .env ------------------------------------------------------
load_dotenv(ROOT / ".env")

# -- Import des modèles (nécessaire pour target_metadata) --------------------
# Seul le domaine audit : le référentiel vit dans une base distincte, avec sa
# propre chaîne (app/migration/).
import app.models.metier  # noqa: E402, F401 — enregistre les tables métier
from app.models.base import BaseAudit  # noqa: E402

target_metadata = BaseAudit.metadata


# -- Construction de l'URL de connexion --------------------------------------
def get_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB_AUDIT"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


# -- Mode online (connexion directe) -----------------------------------------
def run_migrations_online() -> None:
    configuration = context.config.get_section(context.config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
