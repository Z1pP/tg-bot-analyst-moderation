from aiogram import Router

from .templates_menu import router as templates_menu_router

router = Router(name="templates_router")
router.include_router(templates_menu_router)
