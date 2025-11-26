from aiogram import Router

from .add_chat import router as add_chat_router
from .archive import router as archive_router
from .chat_daily_rating import router as chat_daily_rating_router
from .chats_menu import router as chats_menu_router
from .delete_chat import router as delete_chat_router
from .pagination import router as pagination_router
from .select_specific_chat import router as select_specific_chat_router

router = Router(name="chats_router")
router.include_router(add_chat_router)
router.include_router(chats_menu_router)
router.include_router(chat_daily_rating_router)
router.include_router(delete_chat_router)
router.include_router(select_specific_chat_router)
router.include_router(pagination_router)
router.include_router(archive_router)
