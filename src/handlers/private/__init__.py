from aiogram import Router

from .analytics import router as analytics_router
from .categories import router as categories_router
from .chats import router as chats_router
from .common import router as common_router
from .first_time_setup import router as first_time_setup_router
from .message_management import router as message_management_router
from .moderation import router as moderation_router
from .reports import router as reports_router
from .root_menu import router as root_menu_router
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
router.include_router(root_menu_router)
router.include_router(scheduler_router)
router.include_router(first_time_setup_router)
