"""Recalibrate solution/controle to VARCHAR(2048) after scraping fix

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.String(1024),
        type_=sa.String(2048),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.String(1024),
        type_=sa.String(2048),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.String(2048),
        type_=sa.String(1024),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.String(2048),
        type_=sa.String(1024),
        existing_nullable=False,
    )
