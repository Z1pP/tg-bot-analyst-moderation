from aiogram import Router

from .menu_handler import router as menu_router
from .start_handler import router as start_router

router = Router(name="common_router")
router.include_router(menu_router)
router.include_router(start_router)
