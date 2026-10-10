from fastapi import APIRouter

from jev_playground.api import health
from jev_playground.api.v1.router import router as v1_router

router = APIRouter()
router.include_router(health.router)
router.include_router(v1_router, prefix="/api")
