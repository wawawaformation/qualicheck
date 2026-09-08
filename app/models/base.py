from sqlalchemy.orm import DeclarativeBase


class BaseReferentiel(DeclarativeBase):
    """Schéma de la base du référentiel Opquast (245 règles, vecteurs)."""


class BaseAudit(DeclarativeBase):
    """Schéma de la base des données d'audit."""
