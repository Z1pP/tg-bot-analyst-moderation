from aiogram import Router

from .amnesty import router as amnesty_router
from .lock_menu import router as lock_menu_router

router = Router(name="banhammer_router")

router.include_router(lock_menu_router)
router.include_router(amnesty_router)
