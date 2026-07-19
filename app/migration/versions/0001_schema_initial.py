"""Schéma initial — référentiel Opquast + cœur métier QualiCheck

Revision ID: 0001
Revises:
Create Date: 2026-07-18
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Extension pgvector (prérequis à la colonne embedding) ---------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # -- Référentiel Opquast -------------------------------------------------
    op.create_table(
        "objectif",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("objectif", sa.String(256), nullable=False),
    )

    op.create_table(
        "phase",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("phase", sa.String(64), nullable=False),
    )

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tag", sa.String(50), nullable=False),
    )

    op.create_table(
        "regle",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("numero", sa.Integer, nullable=False, unique=True),
        sa.Column("intitule", sa.String(512), nullable=False),
        sa.Column("solution", sa.String(512), nullable=False),
        sa.Column("controle", sa.String(512), nullable=False),
        sa.Column("strategie_analyse", sa.String(20), nullable=False),
        sa.Column("strategie_justification", sa.Text),
        sa.Column("strategie_source", sa.String(20), nullable=False),
        sa.Column("strategie_score", sa.Numeric(3, 2)),
        sa.Column("guide_analyse", sa.Text, nullable=False),
        sa.Column("llm_provider", sa.String(20)),
        sa.Column("embedding", Vector(384)),
    )

    op.create_table(
        "objectif_regle",
        sa.Column("objectif_id", sa.Integer, sa.ForeignKey("objectif.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("objectif_id", "regle_id"),
    )

    op.create_table(
        "phase_regle",
        sa.Column("phase_id", sa.Integer, sa.ForeignKey("phase.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("phase_id", "regle_id"),
    )

    op.create_table(
        "regle_tag",
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id"), nullable=False),
        sa.PrimaryKeyConstraint("regle_id", "tag_id"),
    )

    # -- Cœur métier QualiCheck ----------------------------------------------
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
    )

    op.create_table(
        "audit",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("utilisateur_id", sa.Integer, sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime, nullable=False),
        sa.Column("date_modification", sa.DateTime),
    )

    op.create_table(
        "page",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255)),
    )

    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("page_id", sa.Integer, sa.ForeignKey("page.id"), nullable=False),
        sa.Column("statut_http", sa.String(10)),
        sa.Column("est_selectionnee", sa.Boolean, nullable=False),
        sa.Column("date_crawl", sa.DateTime),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )

    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.PrimaryKeyConstraint("audit_id", "regle_id"),
    )

    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer, sa.ForeignKey("audit.id"), nullable=False),
        sa.Column("page_id", sa.Integer, sa.ForeignKey("page.id"), nullable=False),
        sa.Column("regle_id", sa.Integer, sa.ForeignKey("regle.id"), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512)),
        sa.Column("recommandation", sa.String(512)),
        sa.Column("preuve", sa.String(512)),
        sa.Column("validation_humaine", sa.Boolean),
        sa.Column("feedback_auditeur", sa.Text),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )

    # -- Index ---------------------------------------------------------------
    # HNSW : recherche sémantique RAG (pgvector)
    op.execute("CREATE INDEX ON regle USING hnsw (embedding vector_cosine_ops)")
    # B-tree : performances sur les constats et règles d'un audit
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])


def downgrade() -> None:
    # -- Index ---------------------------------------------------------------
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.execute("DROP INDEX IF EXISTS regle_embedding_idx")

    # -- Tables (ordre inverse des FK) ---------------------------------------
    op.drop_table("constat")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")
    op.drop_table("regle_tag")
    op.drop_table("phase_regle")
    op.drop_table("objectif_regle")
    op.drop_table("regle")
    op.drop_table("tag")
    op.drop_table("phase")
    op.drop_table("objectif")

    # -- Extension -----------------------------------------------------------
    op.execute("DROP EXTENSION IF EXISTS vector")
