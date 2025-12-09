from fastapi import APIRouter

from .health import router as health_router

router = APIRouter(prefix="/internal", tags=["internal"])
router.include_router(health_router)
