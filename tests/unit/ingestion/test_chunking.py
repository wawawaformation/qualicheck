"""
Tests unitaires pour app/ingestion/chunking.py

Teste la construction du texte de chunk (une règle = un chunk, structuré
avec labels).
"""
from app.ingestion.chunking import build_chunk_text, build_combo_text, build_variant_text
from app.ingestion.schema import EnrichedRule


def _rule(contexte=None, objectifs=None, tags=None, phases=None):
    return EnrichedRule(
        id=1, number=1, intitule="Les images ont un attribut alt",
        theme="Contenus", contexte=contexte,
        solution="Ajouter alt descriptif", controle="Vérifier alt présent",
        objectifs=objectifs if objectifs is not None else ["Accessibilité"],
        tags=tags if tags is not None else ["HTML", "Images"],
        phases=phases if phases is not None else ["Intégration"],
        slug="images-alt",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Parcourez le DOM et vérifiez l'attribut alt.",
    )


def test_build_chunk_text_includes_all_labeled_sections():
    """Le chunk contient un label par champ, dans l'ordre attendu."""
    rule = _rule(contexte="Les images décoratives n'ont pas besoin d'alt.")

    chunk = build_chunk_text(rule)

    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Thème : Contenus" in chunk
    assert "Contexte : Les images décoratives n'ont pas besoin d'alt." in chunk
    assert "Solution : Ajouter alt descriptif" in chunk
    assert "Controle : Vérifier alt présent" in chunk
    assert "Guide d'analyse : Parcourez le DOM et vérifiez l'attribut alt." in chunk
    assert "Objectifs : Accessibilité" in chunk
    assert "Tags : HTML, Images" in chunk
    assert "Phases : Intégration" in chunk


def test_build_chunk_text_omits_contexte_when_none():
    """Aucune ligne Contexte si le champ est None."""
    rule = _rule(contexte=None)

    chunk = build_chunk_text(rule)

    assert "Contexte" not in chunk
    assert "Intitulé : Les images ont un attribut alt" in chunk
    assert "Solution : Ajouter alt descriptif" in chunk


def test_build_variant_text_champ_scalaire_renseigne():
    """Un champ texte simple renvoie sa valeur telle quelle."""
    rule = _rule()

    assert build_variant_text(rule, "intitule") == "Les images ont un attribut alt"


def test_build_variant_text_champ_liste_jointe():
    """Une liste (objectifs/tags/phases) est jointe par ', ', même
    convention que build_chunk_text()."""
    rule = _rule(objectifs=["Un", "Deux", "Trois"])

    assert build_variant_text(rule, "objectifs") == "Un, Deux, Trois"


def test_build_variant_text_champ_nullable_vide():
    """Un champ nullable à None retourne None (règle exclue de la variante)."""
    rule = _rule(contexte=None)

    assert build_variant_text(rule, "contexte") is None


def test_build_variant_text_liste_vide():
    """Une liste vide (tags, le seul champ liste sans contrainte de
    non-vacuité) retourne None."""
    rule = _rule(tags=[])

    assert build_variant_text(rule, "tags") is None


def test_build_variant_text_tous_les_champs_de_la_vague_1():
    """Les 11 champs de la vague 1 sont tous lisibles sans erreur."""
    rule = _rule(contexte="Contexte présent")
    champs = [
        "intitule", "theme", "contexte", "solution", "controle",
        "objectifs", "tags", "phases",
        "strategie_analyse", "strategie_justification", "guide_analyse",
    ]

    for champ in champs:
        assert build_variant_text(rule, champ) is not None


def test_build_combo_text_plusieurs_champs_labellises():
    """Une combinaison de plusieurs champs produit un texte labellisé,
    un champ par ligne, dans l'ordre donné."""
    rule = _rule(contexte="Un contexte")

    texte = build_combo_text(rule, ["intitule", "contexte", "objectifs"])

    assert texte == (
        "Intitulé : Les images ont un attribut alt\n"
        "Contexte : Un contexte\n"
        "Objectifs : Accessibilité"
    )


def test_build_combo_text_champ_vide_saute_sans_exclure_la_regle():
    """Un champ vide (contexte=None) est omis de la sortie ; la fonction
    retourne quand même un texte (pas None, contrairement à
    build_variant_text)."""
    rule = _rule(contexte=None)

    texte = build_combo_text(rule, ["intitule", "contexte", "solution"])

    assert texte == (
        "Intitulé : Les images ont un attribut alt\n"
        "Solution : Ajouter alt descriptif"
    )


def test_build_combo_text_champ_liste_jointe():
    """Une liste (objectifs/tags/phases) est jointe par ', ', même
    convention que build_chunk_text/build_variant_text."""
    rule = _rule(objectifs=["Un", "Deux"])

    texte = build_combo_text(rule, ["objectifs"])

    assert texte == "Objectifs : Un, Deux"


def test_build_combo_text_strategie_justification_a_un_label():
    """strategie_justification, absent de build_chunk_text, a son propre
    label — nécessaire pour le candidat E de la vague 2."""
    rule = _rule()

    texte = build_combo_text(rule, ["strategie_justification"])

    assert texte == "Stratégie de justification : Justif"


def test_build_combo_text_tous_les_champs_de_la_vague_2():
    """Les 10 champs utilisés par les 5 combinaisons + la baseline de la
    vague 2 ont tous un label et ne lèvent pas d'erreur."""
    rule = _rule(contexte="Contexte présent")
    champs = [
        "intitule", "theme", "contexte", "solution", "controle",
        "objectifs", "tags", "phases", "strategie_justification", "guide_analyse",
    ]

    texte = build_combo_text(rule, champs)

    for champ_attendu in [
        "Intitulé", "Thème", "Contexte", "Solution", "Controle",
        "Objectifs", "Tags", "Phases", "Stratégie de justification", "Guide d'analyse",
    ]:
        assert f"{champ_attendu} : " in texte
