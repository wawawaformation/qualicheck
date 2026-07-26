"""
Réécriture ciblée des règles marquées pour revue manuelle.

Sélectionne les règles où review_status IS NOT NULL AND != 'valide',
rappelle le LLM d'enrichissement en tenant compte de review_note, puis
vide les champs de revue une fois la correction appliquée.
"""

import json
import logging
from pathlib import Path

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

from .llm_client import LLMClient, load_manifest
from .schema import RuleAggregation
from .stockage import upsert_rule

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


def enrich_again(session: Session, dry_run: bool = False) -> None:
    """
    Rappelle le LLM sur les règles marquées pour revue manuelle et vide
    leurs champs de revue une fois corrigées.

    Fail-fast, commit par règle (pas un commit global) : si une règle
    échoue après ses 3 tentatives, l'exception se propage et arrête le
    traitement — les règles précédentes, déjà commitées individuellement,
    restent acquises.

    Args:
        session: Session SQLAlchemy active
        dry_run: Si True, écrit l'aperçu JSON et s'arrête avant tout appel
            LLM — permet de vérifier les règles concernées sans dépenser

    Raises:
        Exception: Toute erreur d'enrichissement non résolue après les
            tentatives de retry (propagée depuis enrich_single_rule)
    """
    rows = load_rules_to_review(session)

    if not rows:
        progress_logger.info("enrich_again : aucune règle à revoir")
        return

    preview = [
        {"numero": rule.number, "review_note": note, "strategie_analyse_actuelle": current}
        for rule, note, current in rows
    ]
    tmp_dir = Path(__file__).resolve().parents[2] / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    with open(tmp_dir / "enrich_again_preview.json", "w", encoding="utf-8") as f:
        json.dump(preview, f, ensure_ascii=False, indent=2)
    progress_logger.info(f"enrich_again : {len(rows)} règle(s) à revoir")

    if dry_run:
        progress_logger.info("enrich_again : dry-run, aucun appel LLM effectué")
        return

    llm_client = LLMClient()

    try:
        for rule, review_note, current_strategie_analyse in rows:
            try:
                enriched = llm_client.enrich_single_rule(
                    rule,
                    review_note=review_note,
                    current_strategie_analyse=current_strategie_analyse,
                    strategie_source="ia_reingest",
                )
                upsert_rule(session, enriched)
                clear_review_fields(session, numero=rule.number)
                session.commit()
                progress_logger.info(
                    f"Règle {rule.number} — enrich_again : OK "
                    f"({current_strategie_analyse} -> {enriched.strategie_analyse})"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Règle {rule.number} — enrich_again : KO ({e})")
                raise
    finally:
        role = load_manifest()["enrichissement"]
        cost = (
            llm_client.input_tokens * role["prix_entree_par_million"]
            + llm_client.output_tokens * role["prix_sortie_par_million"]
        ) / 1_000_000
        summary = (
            f"enrich_again — Tokens — entrée : {llm_client.input_tokens}, "
            f"sortie : {llm_client.output_tokens}, coût estimé : {cost:.4f} €"
        )
        logger.info(summary)
        progress_logger.info(summary)
