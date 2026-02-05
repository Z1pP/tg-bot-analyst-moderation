from aiogram import Router

from .amnesty import router as amnesty_router
from .block import router as block_user_router
from .menu import router as menu_router
from .warn import router as warn_user_router

router = Router(name="moderation_router")

router.include_router(menu_router)
router.include_router(amnesty_router)
router.include_router(block_user_router)
router.include_router(warn_user_router)
