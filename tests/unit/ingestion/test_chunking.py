"""
Tests unitaires pour app/ingestion/chunking.py

Teste la construction du texte de chunk (une règle = un chunk, structuré
avec labels).
"""
from app.ingestion.chunking import build_chunk_text
from app.ingestion.schema import EnrichedRule


def _rule(contexte=None):
    return EnrichedRule(
        id=1, number=1, intitule="Les images ont un attribut alt",
        theme="Contenus", contexte=contexte,
        solution="Ajouter alt descriptif", controle="Vérifier alt présent",
        objectifs=["Accessibilité"], tags=["HTML", "Images"], phases=["Intégration"],
        slug="images-alt",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Parcourez le DOM et vérifiez l'attribut alt.",
    )


def test_build_chunk_text_includes_all_labeled_sections():
    """Le chunk contient un label par champ, dans l'ordre attendu."""
    rule = _rule(contexte="Les images décoratives n'ont pas besoin d'alt.")

    chunk = build_chunk_text(rule)

    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Contexte : Les images décoratives n'ont pas besoin d'alt." in chunk
    assert "Solution : Ajouter alt descriptif" in chunk
    assert "Controle : Vérifier alt présent" in chunk
    assert "Guide d'analyse : Parcourez le DOM et vérifiez l'attribut alt." in chunk
    assert "Tags : HTML, Images" in chunk
    assert "Phases : Intégration" in chunk


def test_build_chunk_text_omits_contexte_when_none():
    """Aucune ligne Contexte si le champ est None."""
    rule = _rule(contexte=None)

    chunk = build_chunk_text(rule)

    assert "Contexte" not in chunk
    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Solution : Ajouter alt descriptif" in chunk
