from fastapi import APIRouter

from .amnesty import router as amnesty_router
from .analytics import router as analytics_router
from .chats import router as chats_router
from .moderation import router as moderation_router
from .stats import router as stats_router
from .users import router as users_router

router = APIRouter(prefix="/miniapp", tags=["miniapp"])

router.include_router(stats_router)
router.include_router(chats_router)
router.include_router(users_router)
router.include_router(moderation_router)
router.include_router(analytics_router)
router.include_router(amnesty_router)
