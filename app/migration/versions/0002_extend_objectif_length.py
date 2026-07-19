"""Extend objectif column length from 256 to 512

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.String(256),
        type_=sa.String(512),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.String(512),
        type_=sa.String(256),
        existing_nullable=False,
    )
