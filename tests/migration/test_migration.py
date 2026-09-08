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
    "etat_donnees",
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


def test_colonnes_provenance_regle(conn):
    """Les 4 colonnes de provenance doivent exister sur regle, toutes nullables."""
    colonnes = ["llm_model", "prompt_version", "created_at", "updated_at"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'regle'
            AND column_name = ANY(%s);
        """, (colonnes,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    manquantes = set(colonnes) - set(rows)
    assert not manquantes, f"Colonnes provenance manquantes : {manquantes}"
    non_nullable = [col for col in colonnes if rows.get(col) != "YES"]
    assert not non_nullable, f"Colonnes provenance incorrectement NOT NULL : {non_nullable}"


def test_colonnes_revue_manuelle_regle(conn):
    """Les 3 colonnes de revue manuelle doivent exister sur regle, toutes nullables."""
    colonnes = ["reviewed_at", "review_status", "review_note"]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'regle'
            AND column_name = ANY(%s);
        """, (colonnes,))
        rows = {row[0]: row[1] for row in cur.fetchall()}
    manquantes = set(colonnes) - set(rows)
    assert not manquantes, f"Colonnes revue manuelle manquantes : {manquantes}"
    non_nullable = [col for col in colonnes if rows.get(col) != "YES"]
    assert not non_nullable, f"Colonnes revue manuelle incorrectement NOT NULL : {non_nullable}"


def test_colonne_llm_provider_absente(conn):
    """llm_provider doit avoir été renommée en llm_model (colonne absente)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'regle' AND column_name = 'llm_provider';
        """)
        count = cur.fetchone()[0]
    assert count == 0, "llm_provider encore présente — devrait être renommée llm_model"


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


def test_colonne_embedding_dimension_1536(conn):
    """embedding doit être en vector(1536), avec son index HNSW."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            WHERE a.attrelid = 'regle'::regclass AND a.attname = 'embedding';
        """)
        type_actuel = cur.fetchone()[0]
    assert type_actuel == "vector(1536)", f"Type embedding inattendu : {type_actuel}"

    with conn.cursor() as cur:
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'regle' AND indexname = 'regle_embedding_idx';
        """)
        index = cur.fetchone()
    assert index is not None, "Index regle_embedding_idx manquant"


def test_table_etat_donnees(conn):
    """etat_donnees doit exister avec ses colonnes et ses contraintes CHECK."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'etat_donnees'
            ORDER BY ordinal_position;
        """)
        colonnes = cur.fetchall()
    assert colonnes == [
        ("id", "smallint"),
        ("fichier_backup", "character varying"),
        ("type_operation", "character varying"),
        ("horodatage", "timestamp without time zone"),
    ], f"Colonnes inattendues sur etat_donnees : {colonnes}"

    with conn.cursor() as cur:
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'etat_donnees'::regclass AND contype = 'c';
        """)
        contraintes = {row[0] for row in cur.fetchall()}
    assert "etat_donnees_singleton" in contraintes
    assert "etat_donnees_type_operation_check" in contraintes


# -- Isolation du domaine audit -----------------------------------------------

TABLES_DU_DOMAINE_AUDIT = [
    "utilisateur", "audit", "page", "audit_page", "audit_regle", "constat",
]


def test_le_domaine_audit_est_absent_de_cette_base(conn):
    """Preuve d'isolation : les tables métier ont quitté le référentiel."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = {ligne[0] for ligne in curseur.fetchall()}

    restantes = set(TABLES_DU_DOMAINE_AUDIT) & tables
    assert not restantes, f"Tables métier encore présentes : {restantes}"


def test_les_245_regles_sont_intactes(conn):
    """Garde-fou : aucune migration de ce chantier ne touche aux données."""
    with conn.cursor() as curseur:
        curseur.execute(
            "SELECT count(*), count(*) FILTER (WHERE embedding IS NOT NULL) FROM regle;"
        )
        total, vectorisees = curseur.fetchone()

    assert total == 245
    assert vectorisees == 245
