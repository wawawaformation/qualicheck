from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)

from app.models.base import Base


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id = Column(Integer, primary_key=True)
    nom = Column(String(64), nullable=False)
    prenom = Column(String(64), nullable=False)


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    url_depart = Column(String(512), nullable=False)
    statut = Column(String(50), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    date_modification = Column(DateTime)


class Page(Base):
    __tablename__ = "page"

    id = Column(Integer, primary_key=True)
    url = Column(String(512), nullable=False)
    titre = Column(String(255))


class AuditPage(Base):
    __tablename__ = "audit_page"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("page.id"), nullable=False)
    statut_http = Column(String(10))
    est_selectionnee = Column(Boolean, nullable=False)
    date_crawl = Column(DateTime)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "page_id"),
    )


class AuditRegle(Base):
    __tablename__ = "audit_regle"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "regle_id"),
    )


class Constat(Base):
    __tablename__ = "constat"

    audit_id = Column(Integer, ForeignKey("audit.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("page.id"), nullable=False)
    regle_id = Column(Integer, ForeignKey("regle.id"), nullable=False)
    statut = Column(String(32), nullable=False)
    commentaire = Column(String(512))
    recommandation = Column(String(512))
    preuve = Column(String(512))
    validation_humaine = Column(Boolean)
    feedback_auditeur = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("audit_id", "page_id", "regle_id"),
    )
