from aiogram import Router

from .admin_logs import (
    pagination_router as admin_logs_pagination_router,
)
from .admin_logs import (
    router as admin_logs_router,
)
from .analytics import router as analytics_router
from .categories import router as categories_router
from .chats import router as chats_router
from .common import router as common_router
from .message_management import router as message_management_router
from .moderation import router as moderation_router
from .release_notes import router as release_notes_router
from .reports import router as reports_router
from .roles import router as roles_router
from .scheduler import router as scheduler_router
from .templates import router as templates_router
from .users import router as users_router

router = Router(name="private_router")
router.include_router(common_router)
router.include_router(analytics_router)
router.include_router(chats_router)
router.include_router(users_router)
router.include_router(moderation_router)
router.include_router(reports_router)
router.include_router(templates_router)
router.include_router(categories_router)
router.include_router(message_management_router)
router.include_router(admin_logs_router)
router.include_router(admin_logs_pagination_router)
router.include_router(release_notes_router)
router.include_router(roles_router)
router.include_router(scheduler_router)
