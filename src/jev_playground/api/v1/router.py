from fastapi import APIRouter, Depends

from jev_playground.api.security import require_api_key
from jev_playground.modules.ticket_analysis.api.routes import (
    router as ticket_analysis_router,
)

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
router.include_router(ticket_analysis_router)
