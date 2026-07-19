"""
Schémas Pydantic pour le pipeline d'ingestion.

Détail : conception/2_ingestion/ingestion.md
"""

from pydantic import BaseModel, Field, field_validator


class RuleAcquisition(BaseModel):
    """Données brutes acquises pour une règle (API + scraping)."""

    id: int
    number: int
    intitule: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    slug: str
    solution: str | None = Field(default=None)
    controle: str | None = Field(default=None)


class RuleAggregation(BaseModel):
    """Règle complètement validée après agrégation (données requises non-vides)."""

    id: int
    number: int
    intitule: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    slug: str
    solution: str
    controle: str

    @field_validator("objectifs", "tags", "phases")
    @classmethod
    def non_empty_list(cls, v):
        if not v:
            raise ValueError("La liste ne peut pas être vide")
        return v

    @field_validator("intitule", "solution", "controle")
    @classmethod
    def non_empty_string(cls, v):
        if not v or not v.strip():
            raise ValueError("La chaîne ne peut pas être vide")
        return v
    
