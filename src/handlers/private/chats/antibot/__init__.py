"""Antibot handlers package for chat management."""

from aiogram import Router

from .menu import router as antibot_menu_router
from .toggle import router as toggle_antibot_router

antibot_router = Router(name="antibot_router")

antibot_router.include_router(antibot_menu_router)
antibot_router.include_router(toggle_antibot_router)
