"""
Recherche sémantique ad hoc dans les règles Opquast (outil de veille).

Réutilise l'infrastructure pgvector existante (cf. rag_acceptance.py) pour
répondre à une question en langage naturel par les règles les plus proches,
sans jeu de cas ni seuil d'acceptance.
"""

from sqlalchemy.orm import Session

from app.models.referentiel import Regle, Theme


def query_top_n_regles(session: Session, vector: list[float], top_n: int) -> list[dict]:
    """Retourne les top_n règles les plus proches du vecteur (similarité cosinus).

    Chaque résultat contient tous les champs de la règle, le nom du thème
    (résolu) et un score_similarite (1 - distance cosinus).
    """
    distance = Regle.embedding.cosine_distance(vector)
    resultats = (
        session.query(Regle, Theme.theme, distance.label("distance"))
        .join(Theme, Regle.theme_id == Theme.id)
        .order_by(distance)
        .limit(top_n)
        .all()
    )
    return [
        {
            **{col.name: getattr(regle, col.name) for col in Regle.__table__.columns},
            "theme": theme_nom,
            "score_similarite": 1 - distance,
        }
        for regle, theme_nom, distance in resultats
    ]
