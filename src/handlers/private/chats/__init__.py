from aiogram import Router

from .add import router as add_chat_router
from .archive import router as archive_router
from .dashboard import router as dashboard_router
from .list import router as list_chats_router
from .menu import router as chats_menu_router
from .pagination import router as pagination_router
from .rating import router as chat_daily_rating_router
from .untrack import router as untrack_chat_router

router = Router(name="chats_router")
router.include_router(add_chat_router)
router.include_router(chats_menu_router)
router.include_router(chat_daily_rating_router)
router.include_router(untrack_chat_router)
router.include_router(list_chats_router)
router.include_router(dashboard_router)
router.include_router(pagination_router)
router.include_router(archive_router)
