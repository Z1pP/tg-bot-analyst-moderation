from aiogram import Router

from .amnesty import router as amnesty_router
from .block import router as block_user_router
from .navigation import router as navigation_router
from .warn import router as warn_user_router

router = Router(name="moderation_router")

router.include_router(navigation_router)
router.include_router(amnesty_router)
router.include_router(block_user_router)
router.include_router(warn_user_router)
