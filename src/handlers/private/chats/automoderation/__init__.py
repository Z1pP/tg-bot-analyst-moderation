from aiogram import Router

from .settings import router as auto_moderation_settings_router
from .toggle import router as auto_moderation_toggle_router

router = Router(name="auto_moderation_router")

router.include_router(auto_moderation_settings_router)
router.include_router(auto_moderation_toggle_router)
