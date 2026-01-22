"""Antibot handlers package for chat management."""

from aiogram import Router

from .settings import router as antibot_settings_router
from .toggle import router as toggle_antibot_router

antibot_router = Router(name="antibot_router")

antibot_router.include_router(antibot_settings_router)
antibot_router.include_router(toggle_antibot_router)
