from aiogram import Router

from .list_handler import router as moderators_list_router
from .list_of_tracked_handler import router as tracked_chats_list_router

router = Router(name="moderators_router")
router.include_router(moderators_list_router)
router.include_router(tracked_chats_list_router)
