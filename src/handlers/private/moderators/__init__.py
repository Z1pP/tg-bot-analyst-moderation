from aiogram import Router

from .list_handler import router as list_router

router = Router(name="moderators_router")
router.include_router(list_router)
