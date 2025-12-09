from fastapi import APIRouter

from .bot import router as bot_router
from .health import router as health_router

router = APIRouter(prefix="/v1", tags=["v1"])
router.include_router(health_router)
router.include_router(bot_router)
