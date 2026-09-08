"""Retire les six tables métier de la base du référentiel

Elles vivent désormais dans qualicheck_audit, sous leur forme cible
(regle_numero au lieu de regle_id) — voir app/migration_audit/versions/.
Aucune donnée à déplacer : les six tables étaient vides (vérifié le
2026-09-08). Décision et trace du schéma d'avant :
jury/decisions/2026-09-08-deux-bases-referentiel-audit.md

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-08
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ordre inverse des dépendances.
    op.drop_index("ix_constat_audit_id", table_name="constat")
    op.drop_table("constat")
    op.drop_index("ix_audit_regle_audit_id", table_name="audit_regle")
    op.drop_table("audit_regle")
    op.drop_table("audit_page")
    op.drop_table("page")
    op.drop_table("audit")
    op.drop_table("utilisateur")


def downgrade() -> None:
    """Recrée les six tables sous leur forme d'ORIGINE.

    C'est bien la réciproque de cette migration — donc avec regle_id et les
    deux clés étrangères vers regle — et non la forme cible du domaine audit.
    """
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(64), nullable=False),
        sa.Column("prenom", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utilisateur_id", sa.Integer(), nullable=False),
        sa.Column("url_depart", sa.String(512), nullable=False),
        sa.Column("statut", sa.String(50), nullable=False),
        sa.Column("date_creation", sa.DateTime(), nullable=False),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "page",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("titre", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_page",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("statut_http", sa.String(10), nullable=True),
        sa.Column("est_selectionnee", sa.Boolean(), nullable=False),
        sa.Column("date_crawl", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id"),
    )
    op.create_table(
        "audit_regle",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("regle_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["regle_id"], ["regle.id"]),
        sa.PrimaryKeyConstraint("audit_id", "regle_id"),
    )
    op.create_index("ix_audit_regle_audit_id", "audit_regle", ["audit_id"])
    op.create_table(
        "constat",
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("regle_id", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(32), nullable=False),
        sa.Column("commentaire", sa.String(512), nullable=True),
        sa.Column("recommandation", sa.String(512), nullable=True),
        sa.Column("preuve", sa.String(512), nullable=True),
        sa.Column("validation_humaine", sa.Boolean(), nullable=True),
        sa.Column("feedback_auditeur", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["audit.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["page.id"]),
        sa.ForeignKeyConstraint(["regle_id"], ["regle.id"]),
        sa.PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )
    op.create_index("ix_constat_audit_id", "constat", ["audit_id"])
