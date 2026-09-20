"""
API agent US2 (question libre, increment A1b) — étage applicatif qui
consomme l'API des règles en HTTP (app/agent_us2/tools.py), sans toucher
PostgreSQL directement. Contrat :
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent_us2 import api
from app.logging_config import setup_logging
from app.observability.tracing import setup_tracing

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(log_file="logs/agent_us2.log")
    # Au démarrage, une config de traçage invalide doit échouer tout de
    # suite et bruyamment — en cours de requête, get_tracer() dégrade
    # silencieusement plutôt que de casser la réponse.
    setup_tracing(service_name="qualicheck-api-business")
    logger.info("Agent US2 (question libre) démarré")
    yield


app = FastAPI(
    title="QualiCheck — Agent US2 (question libre)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api.router)
