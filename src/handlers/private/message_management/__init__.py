from aiogram import Router

from .action_select_handler import router as action_select_router
from .delete_handler import router as delete_router
from .message_link_handler import router as message_link_router
from .reply_handler import router as reply_router
from .message_manager import router as message_management_router

router = Router()

router.include_router(message_management_router)
router.include_router(message_link_router)
router.include_router(action_select_router)
router.include_router(delete_router)
router.include_router(reply_router)

__all__ = ["router"]
