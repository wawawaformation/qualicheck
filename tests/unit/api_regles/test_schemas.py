"""Schémas et validations de l'API données."""

from datetime import datetime

from app.api_regles.schemas import (
    OutilFiltre,
    RegleRead,
    ReviewStatus,
    ReviewStatusFiltre,
    split_outils,
)
from app.models.referentiel import Regle


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


def _regle_orm(**surcharges) -> Regle:
    """Instance ORM en mémoire, sans session ni base."""
    valeurs = {
        "numero": 124,
        "intitule": "Les contenus audio ne démarrent pas automatiquement",
        "contexte": None,
        "solution": "Ne pas utiliser autoplay",
        "controle": "Charger la page et vérifier",
        "strategie_analyse": "statique&playwright",
        "strategie_justification": "Deux volets indépendants",
        "strategie_source": "ia_reingest",
        "guide_analyse": "Inspecter l'attribut autoplay puis les événements play",
        "prompt_version": 5,
        "llm_model": "kimi-k2.6",
        "review_status": None,
        "review_note": None,
        "reviewed_at": None,
    }
    valeurs.update(surcharges)
    return Regle(**valeurs)


def test_from_regle_derive_les_outils():
    lecture = RegleRead.from_regle(
        _regle_orm(), theme="Contenus", objectifs=["Obj"], tags=["Tag"], phases=["Phase"]
    )

    assert lecture.strategie_analyse == "statique&playwright"
    assert lecture.outils == ["statique", "playwright"]


def test_from_regle_reporte_les_champs_et_les_collections():
    lecture = RegleRead.from_regle(
        _regle_orm(),
        theme="Contenus",
        objectifs=["Objectif A", "Objectif B"],
        tags=["audio"],
        phases=["Production"],
    )

    assert lecture.numero == 124
    assert lecture.theme == "Contenus"
    assert lecture.objectifs == ["Objectif A", "Objectif B"]
    assert lecture.tags == ["audio"]
    assert lecture.phases == ["Production"]
    assert lecture.prompt_version == 5
    assert lecture.llm_model == "kimi-k2.6"


def test_from_regle_expose_letat_de_revue():
    horodatage = datetime(2026, 7, 26, 14, 30)
    lecture = RegleRead.from_regle(
        _regle_orm(
            review_status="a_revoir",
            review_note="Devrait être manuel",
            reviewed_at=horodatage,
        ),
        theme="Contenus",
        objectifs=[],
        tags=[],
        phases=[],
    )

    assert lecture.review_status == "a_revoir"
    assert lecture.review_note == "Devrait être manuel"
    assert lecture.reviewed_at == horodatage


def test_from_regle_nexpose_ni_id_ni_embedding_ni_score():
    lecture = RegleRead.from_regle(
        _regle_orm(), theme="Contenus", objectifs=[], tags=[], phases=[]
    )

    champs = set(lecture.model_dump().keys())
    assert "id" not in champs
    assert "embedding" not in champs
    assert "strategie_score" not in champs
    assert len(champs) == 19
