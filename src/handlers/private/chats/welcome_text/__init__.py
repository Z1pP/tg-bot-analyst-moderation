from aiogram import Router

from .auto_delete_toggle import router as auto_delete_toggle_router
from .change_welcome_text import router as change_welcome_text_router
from .settings import router as welcome_text_settings_router
from .welcome_text_toggle import router as welcome_text_toggle_router

router = Router(name="welcome_text_router")
router.include_router(welcome_text_settings_router)
router.include_router(auto_delete_toggle_router)
router.include_router(welcome_text_toggle_router)
router.include_router(change_welcome_text_router)
