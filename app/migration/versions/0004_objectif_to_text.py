"""Convert objectif column from varchar(512) to text

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.String(512),
        type_=sa.Text,
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.Text,
        type_=sa.String(512),
        existing_nullable=False,
    )
