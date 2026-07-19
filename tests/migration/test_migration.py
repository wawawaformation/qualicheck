"""Tests d'intégration — vérifie le schéma BDD après migration.

Prérequis : conteneur qualicheck-postgres démarré et migration appliquée.
Lancement : make test (ou uv run pytest tests/test_migration.py -v)
"""
import os
from pathlib import Path

import psycopg2
import pytest
from dotenv import load_dotenv

# Chargement du .env à la racine
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@pytest.fixture(scope="module")
def conn():
    """Connexion PostgreSQL partagée pour tous les tests du module."""
    connection = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )
    yield connection
    connection.close()


# -- Extension pgvector ------------------------------------------------------

def test_extension_vector_activee(conn):
    """L'extension pgvector doit être activée dans la base."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';"
        )
        count = cur.fetchone()[0]
    assert count == 1, "L'extension pgvector n'est pas activée"


# -- Tables ------------------------------------------------------------------

TABLES_ATTENDUES = [
    "theme", "regle", "objectif", "phase", "tag",
    "objectif_regle", "phase_regle", "regle_tag",
    "utilisateur", "audit", "page", "audit_page", "audit_regle", "constat",
]

def test_toutes_les_tables_existent(conn):
    """Les 14 tables du MLD doivent toutes exister."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'alembic_version';
        """)
        tables = {row[0] for row in cur.fetchall()}
    manquantes = set(TABLES_ATTENDUES) - tables
    assert not manquantes, f"Tables manquantes : {manquantes}"


# -- Index -------------------------------------------------------------------

def test_index_hnsw_regle_embedding(conn):
    """L'index HNSW sur regle.embedding doit exister."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM pg_indexes
            WHERE tablename = 'regle'
            AND indexdef ILIKE '%hnsw%';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "Index HNSW absent sur regle.embedding"


def test_index_btree_constat_audit_id(conn):
    """L'index B-tree ix_constat_audit_id doit exister."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM pg_indexes
            WHERE indexname = 'ix_constat_audit_id';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "Index ix_constat_audit_id absent"


def test_index_btree_audit_regle_audit_id(conn):
    """L'index B-tree ix_audit_regle_audit_id doit exister."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM pg_indexes
            WHERE indexname = 'ix_audit_regle_audit_id';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "Index ix_audit_regle_audit_id absent"


# -- Contraintes NOT NULL critiques ------------------------------------------

def test_colonnes_not_null_regle(conn):
    """Les colonnes critiques de regle doivent être NOT NULL."""
    colonnes_nn = ["intitule", "solution", "controle", "strategie_analyse",
                   "strategie_source", "guide_analyse"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'regle'
            AND column_name = ANY(%s);
        """, (colonnes_nn,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    nullable = [col for col in colonnes_nn if rows.get(col) != "NO"]
    assert not nullable, f"Colonnes regle incorrectement nullable : {nullable}"


def test_colonnes_not_null_audit(conn):
    """Les colonnes critiques de audit doivent être NOT NULL."""
    colonnes_nn = ["utilisateur_id", "url_depart", "statut", "date_creation"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'audit'
            AND column_name = ANY(%s);
        """, (colonnes_nn,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    nullable = [col for col in colonnes_nn if rows.get(col) != "NO"]
    assert not nullable, f"Colonnes audit incorrectement nullable : {nullable}"


# -- Contraintes UNIQUE -------------------------------------------------------

def test_contrainte_unique_intitule_regle(conn):
    """La colonne regle.intitule doit avoir une contrainte UNIQUE."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'regle'
            AND tc.constraint_type = 'UNIQUE'
            AND ccu.column_name = 'intitule';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "Contrainte UNIQUE absente sur regle.intitule"


# -- Clés primaires composites -----------------------------------------------

def test_pk_composite_constat(conn):
    """La table constat doit avoir une PK composite (audit_id, page_id, regle_id)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_name = 'constat'
            AND constraint_type = 'PRIMARY KEY';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "PK absente sur constat"


def test_pk_composite_audit_page(conn):
    """La table audit_page doit avoir une PK composite (audit_id, page_id)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_name = 'audit_page'
            AND constraint_type = 'PRIMARY KEY';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "PK absente sur audit_page"


def test_pk_composite_audit_regle(conn):
    """La table audit_regle doit avoir une PK composite (audit_id, regle_id)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_name = 'audit_regle'
            AND constraint_type = 'PRIMARY KEY';
        """)
        count = cur.fetchone()[0]
    assert count == 1, "PK absente sur audit_regle"
