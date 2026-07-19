"""Convert solution/controle to TEXT to end the VARCHAR recalibration treadmill

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.String(2048),
        type_=sa.Text,
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.String(2048),
        type_=sa.Text,
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.Text,
        type_=sa.String(2048),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.Text,
        type_=sa.String(2048),
        existing_nullable=False,
    )
