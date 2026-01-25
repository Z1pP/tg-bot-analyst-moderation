from aiogram import Router

from .action_select_handler import router as action_select_router
from .delete_handler import router as delete_router
from .menu import router as menu_router
from .message_link_handler import router as message_link_router
from .reply_handler import router as reply_router
from .send_message_handler import router as send_message_router

router = Router()

router.include_router(menu_router)
router.include_router(message_link_router)
router.include_router(action_select_router)
router.include_router(delete_router)
router.include_router(reply_router)
router.include_router(send_message_router)

__all__ = ["router"]
