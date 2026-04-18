from aiogram import Router

from .settings import router as auto_moderation_settings_router
from .toggle import router as auto_moderation_toggle_router

auto_moderation_router = Router(name="auto_moderation_router")

auto_moderation_router.include_router(auto_moderation_settings_router)
auto_moderation_router.include_router(auto_moderation_toggle_router)

router = auto_moderation_router
