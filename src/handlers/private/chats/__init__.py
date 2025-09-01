from aiogram import Router

from .add_chat import router as add_chat_router
from .delete_chat import router as delete_chat_router
from .list_of_tracked_handler import router as tracked_chats_list_router

router = Router(name="chats_router")
router.include_router(add_chat_router)
router.include_router(delete_chat_router)
router.include_router(tracked_chats_list_router)
