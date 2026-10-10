import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from jev_playground.config import Settings
from jev_playground.modules.ticket_analysis.infrastructure.backends import build_backend

logger = logging.getLogger(__name__)


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.model_ready = False
        backend = build_backend(settings)
        logger.info("loading backend=%s", settings.backend)
        backend.load()
        app.state.backend = backend
        app.state.model_ready = True
        logger.info("backend ready")
        try:
            yield
        finally:
            app.state.model_ready = False
            app.state.backend = None

    return lifespan
