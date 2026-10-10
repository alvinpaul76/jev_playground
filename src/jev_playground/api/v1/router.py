from fastapi import APIRouter, Depends

from jev_playground.api.problem import problem_response
from jev_playground.api.security import require_api_key
from jev_playground.modules.ticket_analysis.api.routes import (
    router as ticket_analysis_router,
)

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
    responses={
        401: problem_response("Missing or invalid X-API-Key."),
        413: problem_response("Request body is too large."),
        500: problem_response("Unexpected error. Quote the request_id when reporting."),
    },
)
router.include_router(ticket_analysis_router)
