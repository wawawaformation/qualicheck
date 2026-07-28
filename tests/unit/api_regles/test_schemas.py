"""Schémas et validations de l'API données."""

from app.api_regles.schemas import OutilFiltre, ReviewStatus, ReviewStatusFiltre, split_outils


def test_strategie_simple_donne_un_seul_outil():
    assert split_outils("manuel") == ["manuel"]
    assert split_outils("statique") == ["statique"]


def test_strategie_composite_et_est_eclatee():
    assert split_outils("statique&playwright") == ["statique", "playwright"]


def test_strategie_composite_puis_est_eclatee():
    assert split_outils("vision+statique") == ["vision", "statique"]


def test_ordre_dapparition_preserve():
    assert split_outils("playwright+vision") == ["playwright", "vision"]


def test_les_quatre_outils_sont_filtrables():
    assert {outil.value for outil in OutilFiltre} == {
        "statique",
        "playwright",
        "vision",
        "manuel",
    }


def test_aucun_est_un_filtre_de_lecture_pas_un_statut_ecrivable():
    """'aucun' signifie review_status IS NULL : il ne s'écrit pas en base."""
    assert "aucun" in {statut.value for statut in ReviewStatusFiltre}
    assert "aucun" not in {statut.value for statut in ReviewStatus}
