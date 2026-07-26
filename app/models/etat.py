from sqlalchemy import CheckConstraint, Column, DateTime, SmallInteger, String

from app.models.base import Base


class EtatDonnees(Base):
    """Ligne unique traçant le dernier export/import de backup appliqué à la base.

    Mise à jour par les cibles Makefile export_sql/import_sql (docker exec
    psql), pas par du code applicatif — le modèle sert à sa lecture (ex.
    futur endpoint FastAPI de statut).
    """

    __tablename__ = "etat_donnees"
    __table_args__ = (
        CheckConstraint("id = 1", name="etat_donnees_singleton"),
        CheckConstraint(
            "type_operation IN ('export', 'import')", name="etat_donnees_type_operation_check"
        ),
    )

    id = Column(SmallInteger, primary_key=True)
    fichier_backup = Column(String(255), nullable=False)
    type_operation = Column(String(10), nullable=False)
    horodatage = Column(DateTime, nullable=False)
