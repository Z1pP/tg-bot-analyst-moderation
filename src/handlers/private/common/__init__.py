from aiogram import Router

from .commands_handler import router as commands_router
from .help_handler import router as help_router
from .menu_handler import router as menu_router
from .start_handler import router as start_router
from .time_router import router as local_time_router

router = Router(name="common_router")
router.include_router(commands_router)
router.include_router(menu_router)
router.include_router(start_router)
router.include_router(help_router)
router.include_router(local_time_router)
