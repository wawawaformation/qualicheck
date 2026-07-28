"""Schémas d'entrée et de sortie de l'API données."""

from enum import Enum

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
