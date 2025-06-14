from aiogram import Router

from .chat_tracking import router as chat_tracking_router
from .select_all_chats import router as all_chats_router
from .select_specific_chat import router as chat_router

router = Router(name="chats_callbacks")
router.include_router(all_chats_router)
router.include_router(chat_router)
router.include_router(chat_tracking_router)
