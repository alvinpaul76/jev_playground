import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from jev_playground.api.errors import register_error_handlers
from jev_playground.api.router import router
from jev_playground.config import Settings
from jev_playground.lifespan import build_lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.auth_enabled and not settings.client_api_keys:
        raise RuntimeError("JEV_CLIENT_API_KEYS must contain at least one key")
    logging.basicConfig(level=settings.log_level)
    if not settings.auth_enabled:
        logging.getLogger(__name__).warning(
            "JEV_AUTH_ENABLED=false: /api/v1/* is open without an API key"
        )
    app = FastAPI(
        title="Ticket Analysis",
        version="0.1.0",
        lifespan=build_lifespan(settings),
        docs_url="/docs" if settings.expose_docs else None,
        redoc_url="/redoc" if settings.expose_docs else None,
        openapi_url="/openapi.json" if settings.expose_docs else None,
    )
    app.state.settings = settings
    app.state.model_ready = False
    app.state.backend = None
    register_error_handlers(app)
    app.include_router(router)
    if settings.expose_docs:

        @app.get("/", include_in_schema=False)
        def root() -> RedirectResponse:
            return RedirectResponse("/docs")

    return app
