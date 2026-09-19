"""
Routeur POST /questions (increment A1b) : expose app/agent_us2/loop.repondre()
en HTTP, conforme au contrat
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.agent_us2.loop import repondre
from app.agent_us2.schemas import QuestionReponse, QuestionRequete, StatutReponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["questions"])


@router.post("/questions", response_model=QuestionReponse)
def poser_question(requete: QuestionRequete) -> QuestionReponse:
    """
    Une question est autonome (pas de mémoire entre questions, increment E1
    plus tard). hors_perimetre n'est pas encore atteignable : voir
    app/agent_us2/schemas.py::StatutReponse.
    """
    try:
        resultat = repondre(requete.question)
    except Exception as e:
        logger.error("Agent indisponible (%s)", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent indisponible",
        ) from e

    statut = (
        StatutReponse.repondu if resultat.regles_citees else StatutReponse.aucune_regle_pertinente
    )

    return QuestionReponse(
        statut=statut,
        reponse=resultat.reponse,
        regles_citees=resultat.regles_citees,
    )
