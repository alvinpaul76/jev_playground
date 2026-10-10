import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from jev_playground.modules.ticket_analysis.domain.errors import (
    ClassifierUnavailable,
    DomainError,
    InvalidBatch,
    InvalidTicket,
)

logger = logging.getLogger(__name__)


class Unauthorized(Exception):
    """Missing or invalid API key. A transport concern, so not a DomainError."""


PROBLEM_JSON = "application/problem+json"
_STATUS: dict[type[DomainError], int] = {
    InvalidBatch: 422,
    InvalidTicket: 422,
    ClassifierUnavailable: 503,
}


def _problem(
    status: int, title: str, detail: str, code: str, request: Request
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=PROBLEM_JSON,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "code": code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error request_id=%s", request_id)
            response = _problem(
                500,
                "Internal server error",
                "An unexpected error occurred.",
                "internal_error",
                request,
            )
        response.headers["x-request-id"] = request_id
        return response


def register_error_handlers(app: FastAPI) -> None:
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(Unauthorized)
    async def handle_unauthorized(request: Request, exc: Unauthorized) -> JSONResponse:
        response = _problem(
            401, "Unauthorized", "A valid API key is required.", "unauthorized", request
        )
        response.headers["WWW-Authenticate"] = "ApiKey"
        return response

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status = _STATUS.get(type(exc), 400)
        if status >= 500:
            logger.warning("domain error code=%s cause=%r", exc.code, exc.__cause__)
        return _problem(status, exc.title, exc.public_message, exc.code, request)
