"""
Étape 4 — Stockage du pipeline d'ingestion.

Persiste chaque EnrichedRule dans PostgreSQL : table regle + tables de
référence (theme, objectif, phase, tag) et leurs associations many-to-many.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.referentiel import (
    Objectif,
    ObjectifRegle,
    Phase,
    PhaseRegle,
    Regle,
    RegleTag,
    Tag,
    Theme,
)

from .aggregation import EnrichedRules
from .schema import EnrichedRule

logger = logging.getLogger(__name__)

TABLES_OPQUAST = [
    "regle_tag",
    "phase_regle",
    "objectif_regle",
    "regle",
    "theme",
    "objectif",
    "phase",
    "tag",
]


def count_rules(session: Session) -> int:
    """Retourne le nombre de règles actuellement stockées."""
    return session.query(Regle).count()


def load_enriched_rules_from_db(session: Session) -> EnrichedRules:
    """
    Charge toutes les règles enrichies depuis la BDD.

    Utile pour reprendre l'ingestion depuis une étape intermédiaire sans
    refaire les étapes 1-4 (acquisition, agrégation, enrichissement LLM, stockage).

    Args:
        session: Session SQLAlchemy active

    Returns:
        Collection EnrichedRules hydratée depuis la BDD

    Raises:
        ValueError: Si la BDD est vide ou incomplète
    """
    regles = session.query(Regle).order_by(Regle.numero).all()

    if not regles:
        raise ValueError("Aucune règle trouvée en BDD — exécuter d'abord une ingestion complète")

    enriched_list = []
    for regle in regles:
        # Récupère les associations many-to-many
        objectifs = (
            session.query(Objectif.objectif)
            .join(ObjectifRegle)
            .filter(ObjectifRegle.regle_id == regle.id)
            .all()
        )
        objectifs_list = [obj[0] for obj in objectifs]

        phases = (
            session.query(Phase.phase)
            .join(PhaseRegle)
            .filter(PhaseRegle.regle_id == regle.id)
            .all()
        )
        phases_list = [phase[0] for phase in phases]

        tags = (
            session.query(Tag.tag)
            .join(RegleTag)
            .filter(RegleTag.regle_id == regle.id)
            .all()
        )
        tags_list = [tag[0] for tag in tags]

        theme = session.query(Theme.theme).filter(Theme.id == regle.theme_id).scalar()

        enriched = EnrichedRule(
            id=regle.id,
            number=regle.numero,
            intitule=regle.intitule,
            theme=theme,
            solution=regle.solution,
            controle=regle.controle,
            objectifs=objectifs_list,
            tags=tags_list,
            phases=phases_list,
            slug="",  # Pas stocké en BDD, laissé vide
            strategie_analyse=regle.strategie_analyse,
            strategie_justification=regle.strategie_justification,
            guide_analyse=regle.guide_analyse,
            strategie_source=regle.strategie_source,
            llm_provider=regle.llm_provider,
        )
        enriched_list.append(enriched)

    enriched_rules = EnrichedRules(enriched_list)
    logger.info(f"Chargement : {len(enriched_list)} règles enrichies depuis la BDD")
    return enriched_rules


def clear_opquast_tables(session: Session) -> None:
    """
    Vide les tables du référentiel Opquast (regle, theme, objectif, phase,
    tag et leurs tables d'association), sans toucher au cœur métier
    QualiCheck (utilisateur, audit, page, constat).
    """
    tables = ", ".join(TABLES_OPQUAST)
    logger.info(f"Vidage des tables Opquast : {tables}")
    session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    session.commit()
    logger.info("Tables Opquast vidées avec succès")


def get_or_create(session: Session, model: type, **kwargs):
    """
    Cherche une ligne existante correspondant à kwargs, la crée si absente.

    Args:
        session: Session SQLAlchemy active
        model: Classe mappée (Theme, Objectif, Phase, ou Tag)
        kwargs: Critères de recherche/création (ex. tag="HTML")

    Returns:
        Instance existante ou nouvellement créée (pas de commit ici)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance

    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance


def upsert_rule(session: Session, enriched_rule: EnrichedRule) -> Regle:
    """
    Insère ou met à jour une Regle (upsert via numero), synchronise ses
    associations (objectif_regle, phase_regle, regle_tag) et son theme_id.

    Si numero existe déjà : UPDATE complet de tous les champs mutables.
    Si numero absent : INSERT.

    Args:
        session: Session SQLAlchemy active
        enriched_rule: Règle enrichie (Étape 3) à persister

    Returns:
        Instance Regle persistée (pas de commit ici)
    """
    regle = session.query(Regle).filter_by(numero=enriched_rule.number).first()
    # Theme résolu avant la création de Regle : get_or_create() interroge la
    # session, ce qui déclenche un autoflush — s'il survenait après
    # session.add(regle), Regle serait flushée avec theme_id encore NULL et
    # violerait la contrainte NOT NULL.
    theme = get_or_create(session, Theme, theme=enriched_rule.theme)

    if regle is None:
        regle = Regle(numero=enriched_rule.number)
        session.add(regle)

    regle.theme_id = theme.id

    regle.intitule = enriched_rule.intitule
    regle.solution = enriched_rule.solution
    regle.controle = enriched_rule.controle
    regle.strategie_analyse = enriched_rule.strategie_analyse
    regle.strategie_justification = enriched_rule.strategie_justification
    regle.strategie_source = enriched_rule.strategie_source
    regle.guide_analyse = enriched_rule.guide_analyse
    regle.llm_provider = enriched_rule.llm_provider

    session.flush()

    # -- Synchronise les associations many-to-many --------------------------
    session.query(ObjectifRegle).filter_by(regle_id=regle.id).delete()
    for objectif_nom in enriched_rule.objectifs:
        objectif = get_or_create(session, Objectif, objectif=objectif_nom)
        session.add(ObjectifRegle(objectif_id=objectif.id, regle_id=regle.id))

    session.query(PhaseRegle).filter_by(regle_id=regle.id).delete()
    for phase_nom in enriched_rule.phases:
        phase = get_or_create(session, Phase, phase=phase_nom)
        session.add(PhaseRegle(phase_id=phase.id, regle_id=regle.id))

    session.query(RegleTag).filter_by(regle_id=regle.id).delete()
    for tag_nom in enriched_rule.tags:
        tag = get_or_create(session, Tag, tag=tag_nom)
        session.add(RegleTag(regle_id=regle.id, tag_id=tag.id))

    session.flush()
    return regle


def store_rules(session: Session, enriched_rules: EnrichedRules) -> None:
    """
    Persiste toute la collection EnrichedRules dans une transaction unique.

    Fail-fast : si une règle échoue, rollback complet (aucune règle
    partiellement stockée), l'exception est relevée.

    Args:
        session: Session SQLAlchemy active
        enriched_rules: Collection EnrichedRules validée (Étape 3)

    Raises:
        Exception: Toute erreur de persistance (relevée après rollback)
    """
    try:
        for rule in enriched_rules.regles:
            upsert_rule(session, rule)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Règle {getattr(rule, 'number', '?')} — stockage : KO ({e})")
        raise

    logger.info(f"Stockage : {len(enriched_rules.regles)} règles stockées")
