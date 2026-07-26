"""Élargit regle.embedding de vector(384) à vector(1536)

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-26
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(384)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")
