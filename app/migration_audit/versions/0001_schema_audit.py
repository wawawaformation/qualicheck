"""Schéma initial du domaine audit

Reprend les six tables métier telles qu'elles existaient dans la base du
référentiel, à une différence près : les liens vers regle passent par le
numero Opquast, sans clé étrangère — une FK ne traverse pas deux bases.
Décision : jury/decisions/2026-09-08-deux-bases-referentiel-audit.md

Revision ID: 0001
Revises:
Create Date: 2026-09-08
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utilisateur_id", sa.Integer(), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime(), nullable=False),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "page",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("statut_http", sa.String(10), nullable=True),
        sa.Column("est_selectionnee", sa.Boolean(), nullable=False),
        sa.Column("date_crawl", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )

    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("regle_numero", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.PrimaryKeyConstraint("audit_id", "regle_numero"),
    )
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])

    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("regle_numero", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512), nullable=True),
        sa.Column("recommandation", sa.String(512), nullable=True),
        sa.Column("preuve", sa.String(512), nullable=True),
        sa.Column("validation_humaine", sa.Boolean(), nullable=True),
        sa.Column("feedback_auditeur", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_numero"),
    )
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])


def downgrade() -> None:
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.drop_table("constat")
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")
