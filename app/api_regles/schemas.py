"""Schémas d'entrée et de sortie de l'API données."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator, model_validator

from app.api_regles import config
from app.models.referentiel import Regle

# La grammaire du prompt d'enrichissement distingue `+` (PUIS — le second volet
# dépend du résultat du premier) et `&` (ET — les deux s'exécutent
# systématiquement). Pour savoir quels outils intervient, les deux se lisent
# pareil ; strategie_analyse reste exposé brut pour ne pas perdre la nuance.
SEPARATEURS_OUTILS = ("&", "+")


class OutilFiltre(str, Enum):
    """Outils filtrables. Valeurs fermées : liste blanche par construction."""

    statique = "statique"
    playwright = "playwright"
    vision = "vision"
    manuel = "manuel"


class ReviewStatusFiltre(str, Enum):
    """Filtres de lecture sur l'état de revue. `aucun` signifie IS NULL."""

    valide = "valide"
    a_revoir = "a_revoir"
    invalide = "invalide"
    aucun = "aucun"


class ReviewStatus(str, Enum):
    """États de revue réellement écrivables en base par le PATCH."""

    valide = "valide"
    a_revoir = "a_revoir"
    invalide = "invalide"


def split_outils(strategie_analyse: str) -> list[str]:
    """Éclate une stratégie composite en ses outils, dans l'ordre d'apparition."""
    morceaux = [strategie_analyse]
    for separateur in SEPARATEURS_OUTILS:
        morceaux = [
            partie for morceau in morceaux for partie in morceau.split(separateur)
        ]
    return [morceau.strip() for morceau in morceaux if morceau.strip()]


class RegleRead(BaseModel):
    """
    Règle enrichie telle qu'exposée aux clients.

    Volontairement absents : id (le numero est la clé publique et il est
    UNIQUE), embedding (1536 flottants inutiles au client), strategie_score
    (vide sur les 245 règles, alimenté par la feedback loop post-MVP),
    created_at et updated_at.
    """

    numero: int
    intitule: str
    theme: str
    contexte: str | None
    solution: str
    controle: str
    strategie_analyse: str
    outils: list[str]
    strategie_justification: str | None
    strategie_source: str
    guide_analyse: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    prompt_version: int | None
    llm_model: str | None
    review_status: str | None
    review_note: str | None
    reviewed_at: datetime | None

    @classmethod
    def from_regle(
        cls,
        regle: Regle,
        theme: str,
        objectifs: list[str],
        tags: list[str],
        phases: list[str],
    ) -> "RegleRead":
        """
        Construit la réponse depuis la ligne ORM et ses collections déjà
        chargées.

        Les collections sont passées explicitement : app/models/ ne déclare
        aucun relationship(), le schéma ne peut donc pas déclencher de
        chargement paresseux involontaire.
        """
        return cls(
            numero=regle.numero,
            intitule=regle.intitule,
            theme=theme,
            contexte=regle.contexte,
            solution=regle.solution,
            controle=regle.controle,
            strategie_analyse=regle.strategie_analyse,
            outils=split_outils(regle.strategie_analyse),
            strategie_justification=regle.strategie_justification,
            strategie_source=regle.strategie_source,
            guide_analyse=regle.guide_analyse,
            objectifs=objectifs,
            tags=tags,
            phases=phases,
            prompt_version=regle.prompt_version,
            llm_model=regle.llm_model,
            review_status=regle.review_status,
            review_note=regle.review_note,
            reviewed_at=regle.reviewed_at,
        )


class ReglePatch(BaseModel):
    """
    Annotation de revue humaine.

    Les trois colonnes review_status / review_note / reviewed_at bougent comme
    un bloc : le PATCH remplace l'annotation entière, il ne modifie pas les
    champs un par un. reviewed_at n'est pas dans le corps — le serveur
    l'horodate, un client ne peut donc ni le falsifier ni l'oublier.
    """

    review_status: ReviewStatus | None
    review_note: str | None = None

    @field_validator("review_note")
    @classmethod
    def valider_la_note(cls, valeur: str | None) -> str | None:
        """
        Refuse ce qui pourrait détourner le prompt d'enrichissement.

        review_note est réinjectée brute par enrich_again dans une section
        « Contexte de revue humaine ». Le prompt délimite ses sections par ##
        et ses exemples par des fences : une note ne doit pouvoir simuler ni
        l'un ni l'autre. On s'arrête là volontairement — traquer des tournures
        comme « ignore les instructions précédentes » est une liste noire
        perdante, la protection réelle étant que seul un porteur du token
        écrit ce champ.
        """
        if valeur is None:
            return None
        if len(valeur) > config.REVIEW_NOTE_MAX_LENGTH:
            raise ValueError(
                f"review_note dépasse {config.REVIEW_NOTE_MAX_LENGTH} caractères"
            )
        if any(ligne.lstrip().startswith("#") for ligne in valeur.splitlines()):
            raise ValueError("review_note ne peut pas contenir de titre markdown")
        if "```" in valeur:
            raise ValueError("review_note ne peut pas contenir de bloc de code")
        return valeur

    @model_validator(mode="after")
    def valider_la_coherence(self) -> "ReglePatch":
        """Une note n'a de sens que là où enrich_again la lira."""
        if self.review_status is None:
            if self.review_note is not None:
                raise ValueError(
                    "review_note est refusée avec review_status=null : annuler "
                    "une annotation n'accepte pas de note"
                )
            return self
        if (
            self.review_status in (ReviewStatus.a_revoir, ReviewStatus.invalide)
            and not self.review_note
        ):
            raise ValueError(
                "review_note est obligatoire pour a_revoir et invalide : "
                "enrich_again l'injecte dans le prompt du LLM"
            )
        return self
