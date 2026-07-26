"""Ajoute la table etat_donnees (provenance du dernier export/import de backup)

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "etat_donnees",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("fichier_backup", sa.String(255), nullable=False),
        sa.Column("type_operation", sa.String(10), nullable=False),
        sa.Column("horodatage", sa.DateTime(), nullable=False),
        sa.CheckConstraint("id = 1", name="etat_donnees_singleton"),
        sa.CheckConstraint(
            "type_operation IN ('export', 'import')", name="etat_donnees_type_operation_check"
        ),
    )


def downgrade() -> None:
    op.drop_table("etat_donnees")
