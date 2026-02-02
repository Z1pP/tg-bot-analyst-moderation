from aiogram import Router

from .menu_handler import router as menu_router
from .reset_settings import router as reset_settings_router
from .start_handler import router as start_router
from .users_chats_settings import router as users_chats_settings_router

router = Router(name="common_router")
router.include_router(menu_router)
router.include_router(start_router)
router.include_router(users_chats_settings_router)
router.include_router(reset_settings_router)
