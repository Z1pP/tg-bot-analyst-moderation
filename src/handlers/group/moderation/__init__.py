from aiogram import Router

from .ban import router as ban_user_router
from .warn import router as warn_user_router

router = Router(name="moderation_router")

router.include_router(ban_user_router)
router.include_router(warn_user_router)
