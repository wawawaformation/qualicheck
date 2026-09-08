"""
Vérifie le schéma réellement en place dans la base du domaine audit.

Lecture seule sur la base de développement du domaine (même exception
assumée que tests/migration/test_migration.py pour le référentiel).
Nécessite : make create-db-audit && make migration-audit.
"""

import os

import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()

TABLES_ATTENDUES = [
    "utilisateur",
    "audit",
    "page",
    "audit_page",
    "audit_regle",
    "constat",
]


@pytest.fixture
def conn():
    connexion = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB_AUDIT"],
    )
    yield connexion
    connexion.close()


def test_toutes_les_tables_du_domaine_existent(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = {ligne[0] for ligne in curseur.fetchall()}

    manquantes = set(TABLES_ATTENDUES) - tables
    assert not manquantes, f"Tables absentes : {manquantes}"


def test_le_referentiel_est_absent_de_cette_base(conn):
    """Preuve d'isolation : la table regle n'est pas joignable depuis ici."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT to_regclass('public.regle') IS NULL, to_regclass('public.theme') IS NULL;"
        )
        regle_absente, theme_absent = curseur.fetchone()

    assert regle_absente, "La table regle ne doit pas exister dans la base d'audit"
    assert theme_absent, "La table theme ne doit pas exister dans la base d'audit"


def test_aucune_fk_ne_sort_du_domaine(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT conrelid::regclass::text, confrelid::regclass::text
            FROM pg_constraint
            WHERE contype = 'f';
            """
        )
        liens = curseur.fetchall()

    cibles_hors_domaine = {
        cible for _, cible in liens if cible not in TABLES_ATTENDUES
    }
    assert not cibles_hors_domaine, f"FK vers l'extérieur : {cibles_hors_domaine}"


def test_pk_composite_audit_regle(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT string_agg(a.attname, ',' ORDER BY k.ord)
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.conrelid = 'audit_regle'::regclass AND c.contype = 'p';
            """
        )
        assert curseur.fetchone()[0] == "audit_id,regle_numero"


def test_pk_composite_constat(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT string_agg(a.attname, ',' ORDER BY k.ord)
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.conrelid = 'constat'::regclass AND c.contype = 'p';
            """
        )
        assert curseur.fetchone()[0] == "audit_id,page_id,regle_numero"


def test_index_btree_constat_audit_id(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_constat_audit_id';"
        )
        assert curseur.fetchone()[0] == 1


def test_index_btree_audit_regle_audit_id(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_audit_regle_audit_id';"
        )
        assert curseur.fetchone()[0] == 1


def test_colonnes_not_null_audit(conn):
    with conn.cursor() as curseur:
        curseur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'audit'
              AND column_name IN ('utilisateur_id', 'url_depart', 'statut', 'date_creation')
              AND is_nullable = 'YES';
            """
        )
        nullable = [ligne[0] for ligne in curseur.fetchall()]

    assert not nullable, f"Colonnes audit incorrectement nullable : {nullable}"
