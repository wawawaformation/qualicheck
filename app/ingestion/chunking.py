"""
Construction du texte de chunk pour l'embedding.

Une règle = un chunk (décision actée, cf.
conception/2_us0/ingestion/L_chunking_embedding_indexation.md §3 et
conception/2_us0/ingestion/ingestion.md §Étape 5) : le texte assemble tous les
champs pertinents d'une règle, structuré avec des labels par champ.
"""


def build_chunk_text(rule) -> str:
    """
    Assemble le texte structuré d'un chunk à partir des champs d'une règle.

    Args:
        rule: objet portant intitule, theme, contexte, solution, controle,
            guide_analyse, objectifs, tags, phases (ex. EnrichedRule)

    Returns:
        Texte structuré avec labels, une section par champ. La section
        "Contexte" est omise si rule.contexte est None.
    """
    parts = [f"Intitulé : {rule.intitule}"]
    parts.append(f"Thème : {rule.theme}")
    if rule.contexte:
        parts.append(f"Contexte : {rule.contexte}")
    parts.append(f"Solution : {rule.solution}")
    parts.append(f"Controle : {rule.controle}")
    parts.append(f"Guide d'analyse : {rule.guide_analyse}")
    parts.append(f"Objectifs : {', '.join(rule.objectifs)}")
    parts.append(f"Tags : {', '.join(rule.tags)}")
    parts.append(f"Phases : {', '.join(rule.phases)}")
    return "\n".join(parts)


def build_variant_text(rule, champ: str) -> str | None:
    """
    Texte d'un seul champ de la règle, pour l'étude d'ablation des
    variantes de chunk (scripts/mesure_variantes_chunks.py, voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md).

    Args:
        rule: objet portant les mêmes attributs qu'EnrichedRule
        champ: nom de l'attribut à extraire (ex. "intitule", "guide_analyse")

    Returns:
        Le texte du champ, ou None s'il est vide/absent — la règle est
        alors exclue de cette variante (pas de texte vide envoyé à l'API
        d'embedding).
    """
    valeur = getattr(rule, champ)
    if isinstance(valeur, list):
        return ", ".join(valeur) if valeur else None
    return valeur if valeur else None


def build_combo_text(rule, champs: list[str]) -> str:
    """
    Texte labellisé d'une combinaison de champs, pour l'étude de
    combinaisons de chunk (scripts/mesure_combinaisons_chunks.py, voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md).

    Args:
        rule: objet portant les mêmes attributs qu'EnrichedRule
        champs: noms des attributs à inclure, dans l'ordre donné

    Returns:
        Texte structuré avec labels, une section par champ non vide.
        Un champ vide est omis (même convention que le traitement
        optionnel de "Contexte" dans build_chunk_text) — contrairement à
        build_variant_text, la règle n'est jamais exclue : ne retourne
        jamais None.
    """
    labels = {
        "intitule": "Intitulé",
        "theme": "Thème",
        "contexte": "Contexte",
        "solution": "Solution",
        "controle": "Controle",
        "objectifs": "Objectifs",
        "tags": "Tags",
        "phases": "Phases",
        "strategie_justification": "Stratégie de justification",
        "guide_analyse": "Guide d'analyse",
    }
    parts = []
    for champ in champs:
        valeur = getattr(rule, champ)
        texte = ", ".join(valeur) if isinstance(valeur, list) else valeur
        if texte:
            parts.append(f"{labels[champ]} : {texte}")
    return "\n".join(parts)
