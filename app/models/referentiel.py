from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
)

from app.models.base import Base


class Theme(Base):
    __tablename__ = "theme"

    id = Column(Integer, primary_key=True)
    theme = Column(String(64), nullable=False, unique=True)


class Regle(Base):
    __tablename__ = "regle"

    id = Column(Integer, primary_key=True)
    theme_id = Column(Integer, ForeignKey("theme.id"), nullable=False)
    numero = Column(Integer, nullable=False, unique=True)
    intitule = Column(String(255), nullable=False, unique=True)
    contexte = Column(Text, nullable=True)
    solution = Column(Text, nullable=False)
    controle = Column(Text, nullable=False)
    strategie_analyse = Column(String(32), nullable=False)
    strategie_justification = Column(Text)
    strategie_source = Column(String(32), nullable=False)
    strategie_score = Column(Numeric(3, 2))
    guide_analyse = Column(Text, nullable=False)
    llm_model = Column(String(64), nullable=True)
    prompt_version = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_status = Column(String(16), nullable=True)
    review_note = Column(Text, nullable=True)
    embedding = Column(Vector(384))


class Objectif(Base):
    __tablename__ = "objectif"

    id = Column(Integer, primary_key=True)
    objectif = Column(String(512), nullable=False)


class Phase(Base):
    __tablename__ = "phase"

    id = Column(Integer, primary_key=True)
    phase = Column(String(64), nullable=False)


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False)


class ObjectifRegle(Base):
    __tablename__ = "objectif_regle"

    objectif_id = Column(Integer, ForeignKey("objectif.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("objectif_id", "regle_id"),
    )


class PhaseRegle(Base):
    __tablename__ = "phase_regle"

    phase_id = Column(Integer, ForeignKey("phase.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("phase_id", "regle_id"),
    )


class RegleTag(Base):
    __tablename__ = "regle_tag"

    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("regle_id", "tag_id"),
    )
