import logging
import secrets
from typing import Annotated

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from jev_playground.api.errors import Unauthorized

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    request: Request, presented: Annotated[str | None, Security(api_key_header)]
) -> None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return
    configured = settings.client_api_keys
    matched = False
    for key in configured:  # no early exit: timing must not reveal which key was close
        if presented is not None and secrets.compare_digest(
            presented.encode(), key.get_secret_value().encode()
        ):
            matched = True
    if not matched:
        logger.warning(
            "rejected api key request_id=%s client=%s",
            getattr(request.state, "request_id", None),
            request.client.host if request.client else None,
        )
        raise Unauthorized()
