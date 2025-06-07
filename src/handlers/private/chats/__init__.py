from aiogram import Router

from .list_handler import router as moderators_list_router

router = Router(name="moderators_router")
router.include_router(moderators_list_router)
