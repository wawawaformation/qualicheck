"""Router des règles enrichies."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Query as OrmQuery
from sqlalchemy.orm import Session

from app.api_regles.auth import require_bearer
from app.api_regles.schemas import OutilFiltre, ReglePatch, RegleRead, ReviewStatusFiltre
from app.db import get_session
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regles", tags=["regles"])


def _libelles_par_regle(
    session: Session,
    colonne_regle_id,
    colonne_libelle,
    condition_appariement,
    regle_ids: list[int],
) -> dict[int, list[str]]:
    """
    {regle_id: [libellés]} pour une collection N:N, en UNE seule requête.

    app/models/ ne déclare aucun relationship() : les jointures s'écrivent à la
    main. Appelée une fois par collection — 3 requêtes au total, quel que soit
    le nombre de règles. Le motif naïf (une requête par collection et par
    règle, comme enrich_again.load_rules_to_review) produirait 736 requêtes sur
    245 règles.
    """
    if not regle_ids:
        return {}

    lignes = (
        session.query(colonne_regle_id, colonne_libelle)
        .filter(condition_appariement, colonne_regle_id.in_(regle_ids))
        .all()
    )

    groupes: dict[int, list[str]] = {}
    for regle_id, libelle in lignes:
        groupes.setdefault(regle_id, []).append(libelle)
    return groupes


def _charger_regles(session: Session, requete: OrmQuery) -> list[RegleRead]:
    """
    Assemble les réponses depuis une requête déjà filtrée renvoyant des
    couples (Regle, libellé de thème). Coût total : 4 requêtes.
    """
    lignes = requete.all()
    regle_ids = [regle.id for regle, _ in lignes]

    tags = _libelles_par_regle(
        session, RegleTag.regle_id, Tag.tag, Tag.id == RegleTag.tag_id, regle_ids
    )
    phases = _libelles_par_regle(
        session,
        PhaseRegle.regle_id,
        Phase.phase,
        Phase.id == PhaseRegle.phase_id,
        regle_ids,
    )
    objectifs = _libelles_par_regle(
        session,
        ObjectifRegle.regle_id,
        Objectif.objectif,
        Objectif.id == ObjectifRegle.objectif_id,
        regle_ids,
    )

    return [
        RegleRead.from_regle(
            regle,
            theme=theme,
            objectifs=objectifs.get(regle.id, []),
            tags=tags.get(regle.id, []),
            phases=phases.get(regle.id, []),
        )
        for regle, theme in lignes
    ]


@router.get("", response_model=list[RegleRead])
def lister_regles(
    session: Session = Depends(get_session),
    outil: list[OutilFiltre] = Query(default=[]),
    review_status: list[ReviewStatusFiltre] = Query(default=[]),
) -> list[RegleRead]:
    """
    Les règles enrichies, triées par numéro.

    Sans paramètre : les 245 règles (~500 kB). Aucune pagination — le corpus
    Opquast est figé. Les deux filtres sont des OU en interne, un ET entre eux.
    """
    requete = (
        session.query(Regle, Theme.theme)
        .filter(Theme.id == Regle.theme_id)
        .order_by(Regle.numero)
    )

    if outil:
        # « contient l'outil », pas « égale » : 85 règles contiennent playwright
        # via les valeurs composites, contre 62 en égalité stricte. contains()
        # produit un LIKE à paramètre lié, et les valeurs viennent d'un Enum —
        # liste blanche par construction.
        requete = requete.filter(
            or_(*[Regle.strategie_analyse.contains(valeur.value) for valeur in outil])
        )

    if review_status:
        conditions = [
            Regle.review_status.is_(None)
            if statut is ReviewStatusFiltre.aucun
            else Regle.review_status == statut.value
            for statut in review_status
        ]
        requete = requete.filter(or_(*conditions))

    return _charger_regles(session, requete)


@router.get("/{numero}", response_model=RegleRead)
def lire_regle(
    numero: int,
    session: Session = Depends(get_session),
) -> RegleRead:
    """Une règle enrichie, désignée par son numéro Opquast."""
    requete = session.query(Regle, Theme.theme).filter(
        Theme.id == Regle.theme_id, Regle.numero == numero
    )
    lectures = _charger_regles(session, requete)

    if not lectures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Règle {numero} inconnue",
        )
    return lectures[0]


@router.patch("/{numero}", response_model=RegleRead)
def annoter_regle(
    numero: int,
    annotation: ReglePatch,
    session: Session = Depends(get_session),
    client_nom: str = Depends(require_bearer),
) -> RegleRead:
    """
    Pose ou retire l'annotation de revue humaine d'une règle.

    N'écrit QUE review_status / review_note / reviewed_at : le référent
    annote, il ne réécrit pas l'enrichissement. La correction elle-même est un
    autre geste, fait plus tard par un développeur via make enrich-again — le
    seul à appeler le LLM et à coûter de l'argent.
    """
    regle = session.query(Regle).filter(Regle.numero == numero).one_or_none()
    if regle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Règle {numero} inconnue",
        )

    if annotation.review_status is None:
        # Annulation : les trois colonnes repartent à NULL, exactement comme le
        # fait enrich_again après une correction réussie.
        regle.review_status = None
        regle.review_note = None
        regle.reviewed_at = None
    else:
        regle.review_status = annotation.review_status.value
        regle.review_note = annotation.review_note
        # Horodatage serveur, jamais accepté du client : ni falsifiable ni
        # oubliable. Même forme que app/ingestion/stockage.py.
        regle.reviewed_at = datetime.now(UTC).replace(tzinfo=None)

    session.commit()

    logger.info(
        "Règle %s annotée par %s : review_status=%s", numero, client_nom, regle.review_status
    )

    requete = session.query(Regle, Theme.theme).filter(
        Theme.id == Regle.theme_id, Regle.numero == numero
    )
    return _charger_regles(session, requete)[0]
