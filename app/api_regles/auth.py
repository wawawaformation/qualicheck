"""Garde d'écriture de l'API données."""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api_regles import config

# auto_error=False : le comportement par défaut de HTTPBearer renvoie un 403
# quand le header est absent. Or aucune identité n'a été fournie — c'est un 401.
_schema = HTTPBearer(auto_error=False)


def require_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_schema),
) -> str:
    """
    Vérifie le token Bearer contre chaque client déclaré, renvoie son nom.

    Garde d'écriture : plusieurs jetons possibles (un par client), pas de rôle
    ni de session — d'où 401 (identité absente ou invalide) et non 403.
    """
    if credentials is not None:
        for nom, jeton in config.clients_tokens().items():
            # compare_digest : une comparaison naïve (==) s'arrête au premier
            # caractère différent et laisse fuiter la longueur du préfixe
            # correct par le temps de réponse. Bibliothèque standard.
            if secrets.compare_digest(credentials.credentials, jeton):
                return nom
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token Bearer absent ou invalide",
    )
