"""
API données : accès HTTP au référentiel Opquast enrichi.

Étage données de l'architecture n-tiers. L'étage applicatif (app/api_business/,
US1 et US2) consommera cette API en HTTP et ne touchera pas PostgreSQL.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api_regles import config, regles
from app.db import get_session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Fail-fast : sans secret d'écriture, la clé attendue serait vide et le
    PATCH ouvert à tous. Volontairement au démarrage réel du serveur
    (uvicorn), pas à l'import du module — sinon tout test qui importe
    l'application (TestClient) dépendrait d'un vrai secret présent dans
    l'environnement, y compris pour des tests qui n'exercent jamais le
    PATCH. `TestClient(app)` sans bloc `with` ne déclenche pas ce cycle de
    vie, contrairement à `uv run uvicorn` (make api-regles).
    """
    config.clients_tokens()
    yield


app = FastAPI(
    title=config.TITLE,
    # L'attribution est ajoutée à la description pour qu'un client qui ne lit
    # que la page Swagger la voie, en plus du champ license_info.
    description=f"{config.DESCRIPTION}\n\n{config.ATTRIBUTION}",
    version=config.VERSION,
    # Champ standard OpenAPI. Obligation de CC BY-SA 4.0, la licence du
    # référentiel Opquast que cette API distribue — pas une politesse.
    license_info={"name": config.LICENCE_NOM, "url": config.LICENCE_URL},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Jamais ["*"] : n'importe quel site pourrait faire lire le corpus enrichi
    # par le navigateur d'un visiteur.
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "PATCH"],
    # Authorization est indispensable, sinon le préflight du PATCH échoue.
    allow_headers=["Authorization", "Content-Type"],
    # L'authentification passe par un header, pas par un cookie : les attaques
    # CSRF par cookie ne s'appliquent pas.
    allow_credentials=False,
)

app.include_router(regles.router)


@app.get("/health", tags=["infrastructure"])
def health(session: Session = Depends(get_session)):
    """
    Sonde de santé : vérifie que la base répond, pas seulement le processus.

    Le seul travail de cette API étant de lire la base, une sonde qui
    l'ignorerait déclarerait l'API en bonne santé alors qu'elle serait
    incapable de servir la moindre règle.
    """
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "base": "injoignable"},
        )
    return {"status": "ok", "base": "ok", "version": config.VERSION}
