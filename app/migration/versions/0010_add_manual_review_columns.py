"""Add manual review columns to regle (reviewed_at, review_status, review_note)

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("regle", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("regle", sa.Column("review_status", sa.String(16), nullable=True))
    op.add_column("regle", sa.Column("review_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("regle", "review_note")
    op.drop_column("regle", "review_status")
    op.drop_column("regle", "reviewed_at")
