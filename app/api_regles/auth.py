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
) -> None:
    """
    Vérifie le token Bearer. Ne renvoie rien : laisse passer ou lève 401.

    Garde d'écriture, pas un rôle : il n'y a pas d'identité, seulement un
    secret partagé — d'où 401 et non 403.
    """
    attendu = config.admin_token()
    # compare_digest : une comparaison naïve (==) s'arrête au premier caractère
    # différent et laisse fuiter la longueur du préfixe correct par le temps de
    # réponse. Bibliothèque standard, aucune dépendance ajoutée.
    if credentials is None or not secrets.compare_digest(
        credentials.credentials, attendu
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer absent ou invalide",
        )
