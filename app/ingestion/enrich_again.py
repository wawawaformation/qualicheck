"""
Réécriture ciblée des règles marquées pour revue manuelle.

Sélectionne les règles où review_status IS NOT NULL AND != 'valide',
rappelle le LLM d'enrichissement en tenant compte de review_note, puis
vide les champs de revue une fois la correction appliquée.
"""

import logging

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

from .schema import RuleAggregation

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")


def load_rules_to_review(session: Session) -> list[tuple[RuleAggregation, str, str]]:
    """
    Charge les règles marquées pour revue manuelle (a_revoir ou invalide).

    Args:
        session: Session SQLAlchemy active

    Returns:
        Liste de triplets (règle reconstituée, review_note, strategie_analyse
        actuelle), dans l'ordre des numéros.
    """
    regles = (
        session.query(Regle)
        .filter(Regle.review_status.isnot(None), Regle.review_status != "valide")
        .order_by(Regle.numero)
        .all()
    )

    result = []
    for regle in regles:
        objectifs = (
            session.query(Objectif.objectif)
            .join(ObjectifRegle)
            .filter(ObjectifRegle.regle_id == regle.id)
            .all()
        )
        phases = (
            session.query(Phase.phase)
            .join(PhaseRegle)
            .filter(PhaseRegle.regle_id == regle.id)
            .all()
        )
        tags = (
            session.query(Tag.tag)
            .join(RegleTag)
            .filter(RegleTag.regle_id == regle.id)
            .all()
        )
        theme = session.query(Theme.theme).filter(Theme.id == regle.theme_id).scalar()

        rule = RuleAggregation(
            id=regle.id,
            number=regle.numero,
            intitule=regle.intitule,
            theme=theme,
            contexte=regle.contexte,
            solution=regle.solution,
            controle=regle.controle,
            objectifs=[o[0] for o in objectifs],
            tags=[t[0] for t in tags],
            phases=[p[0] for p in phases],
            slug="",
        )
        result.append((rule, regle.review_note, regle.strategie_analyse))

    return result


def clear_review_fields(session: Session, numero: int) -> None:
    """
    Remet reviewed_at/review_status/review_note à NULL pour une règle.

    Pas de commit ici — reste dans la même transaction que l'upsert qui
    a corrigé la règle (voir enrich_again()).

    Args:
        session: Session SQLAlchemy active
        numero: Numéro de la règle à nettoyer
    """
    regle = session.query(Regle).filter_by(numero=numero).first()
    if regle is None:
        return
    regle.reviewed_at = None
    regle.review_status = None
    regle.review_note = None
    session.flush()
