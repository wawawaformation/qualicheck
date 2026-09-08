"""Crée la base du domaine audit si elle n'existe pas déjà.

PostgreSQL n'a pas de CREATE DATABASE IF NOT EXISTS : on teste la présence
dans pg_database avant de créer. Idempotent, donc rejouable sans condition —
un seul mécanisme utilisé aussi bien en local qu'en CI, plutôt qu'un script
d'init Docker qui ne s'exécuterait que sur un volume vierge.

Le nom de la base vient de POSTGRES_DB_AUDIT ; le surcharger permet de créer
la base de test du même domaine.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.sql import SQL, Identifier

load_dotenv()


def main() -> None:
    nom = os.environ["POSTGRES_DB_AUDIT"]

    # CREATE DATABASE ne peut pas tourner dans une transaction : on se
    # connecte à la base d'administration en autocommit.
    connexion = psycopg2.connect(
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname="postgres",
    )
    connexion.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (nom,))
            if curseur.fetchone():
                print(f"Base « {nom} » déjà présente, rien à faire.")
                return

            # Identifier() échappe le nom, qui vient de l'environnement.
            curseur.execute(SQL("CREATE DATABASE {}").format(Identifier(nom)))
            print(f"Base « {nom} » créée.")
    finally:
        connexion.close()


if __name__ == "__main__":
    sys.exit(main())
