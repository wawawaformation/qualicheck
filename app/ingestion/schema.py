"""
Schéma de données pour l'acquisition des règles (API + scraping Opquast).

Utilise Pydantic pour la validation. Détail : conception/2_ingestion/ingestion.md
"""

from pydantic import BaseModel, Field


class RuleAcquisition(BaseModel):
    id: int
    number: int
    intitule: str  # vient de description.fr
    objectifs: list[str]  # vient de goal.fr
    tags: list[str]  # vient de metadata.Tags
    phases: list[str]  # vient de metadata["Phases projet"]
    slug: str  # vient de slug.fr
    solution: str | None = Field(default=None)  # extrait du scraping
    controle: str | None = Field(default=None)  # extrait du scraping
    
