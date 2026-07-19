"""Convert regle text columns from varchar to text

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regle",
        "intitule",
        existing_type=sa.String(512),
        type_=sa.Text,
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.String(512),
        type_=sa.Text,
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.String(512),
        type_=sa.Text,
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.Text,
        type_=sa.String(512),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.Text,
        type_=sa.String(512),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "intitule",
        existing_type=sa.Text,
        type_=sa.String(512),
        existing_nullable=False,
    )
