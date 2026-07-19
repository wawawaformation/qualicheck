"""Final schema calibration based on real data measurements

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Regle columns calibrated from real data (245 rules)
    op.alter_column(
        "regle",
        "intitule",
        existing_type=sa.Text,
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.Text,
        type_=sa.String(1024),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.Text,
        type_=sa.String(1024),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "strategie_analyse",
        existing_type=sa.String(20),
        type_=sa.String(32),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "strategie_source",
        existing_type=sa.String(20),
        type_=sa.String(32),
        existing_nullable=False,
    )

    # Objectif column calibrated from real data
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.Text,
        type_=sa.String(512),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "objectif",
        "objectif",
        existing_type=sa.String(512),
        type_=sa.Text,
        existing_nullable=False,
    )

    op.alter_column(
        "regle",
        "strategie_source",
        existing_type=sa.String(32),
        type_=sa.String(20),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "strategie_analyse",
        existing_type=sa.String(32),
        type_=sa.String(20),
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "controle",
        existing_type=sa.String(1024),
        type_=sa.Text,
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "solution",
        existing_type=sa.String(1024),
        type_=sa.Text,
        existing_nullable=False,
    )
    op.alter_column(
        "regle",
        "intitule",
        existing_type=sa.String(255),
        type_=sa.Text,
        existing_nullable=False,
    )
