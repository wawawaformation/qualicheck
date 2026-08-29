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
        rule: objet portant intitule, contexte, solution, controle,
            guide_analyse, tags, phases (ex. EnrichedRule)

    Returns:
        Texte structuré avec labels, une section par champ. La section
        "Contexte" est omise si rule.contexte est None.
    """
    parts = [f"Intitulé : {rule.intitule}"]
    if rule.contexte:
        parts.append(f"Contexte : {rule.contexte}")
    parts.append(f"Solution : {rule.solution}")
    parts.append(f"Controle : {rule.controle}")
    parts.append(f"Guide d'analyse : {rule.guide_analyse}")
    parts.append(f"Tags : {', '.join(rule.tags)}")
    parts.append(f"Phases : {', '.join(rule.phases)}")
    return "\n".join(parts)
