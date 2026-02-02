from aiogram import Router

from .archive import router as archive_bind_router
from .common import router as group_common_router
from .left_member import router as left_member_router
from .moderation import router as moderation_router
from .new_members import router as new_members_router
from .new_message import router as message_router
from .query_handler import router as inline_query_router
from .reactions import router as reactions_router
from .track_chat import router as track_chat_router
from .untrack_chat import router as untrack_chat_router

router = Router(name="group_router")
router.include_router(moderation_router)
router.include_router(group_common_router)
router.include_router(archive_bind_router)
router.include_router(new_members_router)
router.include_router(left_member_router)
router.include_router(inline_query_router)
router.include_router(track_chat_router)
router.include_router(untrack_chat_router)
router.include_router(message_router)
router.include_router(reactions_router)
