"""Rename llm_provider to llm_model, add prompt_version/created_at/updated_at

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regle",
        "llm_provider",
        existing_type=sa.String(20),
        type_=sa.String(64),
        existing_nullable=True,
    )
    op.alter_column(
        "regle",
        "llm_provider",
        new_column_name="llm_model",
        existing_type=sa.String(64),
    )
    op.add_column("regle", sa.Column("prompt_version", sa.Integer(), nullable=True))
    op.add_column("regle", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("regle", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("regle", "updated_at")
    op.drop_column("regle", "created_at")
    op.drop_column("regle", "prompt_version")
    op.alter_column(
        "regle",
        "llm_model",
        new_column_name="llm_provider",
        existing_type=sa.String(64),
    )
    op.alter_column(
        "regle",
        "llm_provider",
        existing_type=sa.String(64),
        type_=sa.String(20),
        existing_nullable=True,
    )
