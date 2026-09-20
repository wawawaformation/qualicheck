"""
Schémas Pydantic de l'API agent US2 (increment A1b) — miroir de
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json,
contrat vivant enrichi increment par increment.
"""

from enum import Enum

from pydantic import BaseModel, Field


class StatutReponse(str, Enum):
    """
    hors_perimetre n'est jamais renvoyé pour l'instant : ce statut suppose
    un contrôle de sujet (increment C5, pas encore construit). Il existe
    déjà ici pour ne pas casser le contrat quand C5 arrivera.

    service_indisponible : la question est dans le sujet, mais un service dont
    l'agent dépend (l'API des règles) était en panne (HTTP 200, pas un 503).
    """

    repondu = "repondu"
    aucune_regle_pertinente = "aucune_regle_pertinente"
    hors_perimetre = "hors_perimetre"
    service_indisponible = "service_indisponible"


class QuestionRequete(BaseModel):
    question: str = Field(..., description="Question libre en langage naturel")


class RegleCitee(BaseModel):
    numero: int
    intitule: str


class QuestionReponse(BaseModel):
    statut: StatutReponse
    reponse: str
    regles_citees: list[RegleCitee]
    trace_id: str | None = None
