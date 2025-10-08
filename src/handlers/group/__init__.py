from aiogram import Router

from .moderation import router as moderation_router
from .chat_tracking_handler import router as chat_tracking_router
from .message_handler import router as message_router
from .new_members import router as new_members_router
from .query_handler import router as inline_query_router
from .reactions import router as reactions_router

router = Router(name="group_router")
router.include_router(new_members_router)
router.include_router(inline_query_router)
router.include_router(chat_tracking_router)
router.include_router(moderation_router)
router.include_router(message_router)
router.include_router(reactions_router)
