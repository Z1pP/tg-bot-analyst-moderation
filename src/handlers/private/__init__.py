from aiogram import Router

from .categories import router as categories_router
from .chats import router as chats_router
from .common import router as common_router
from .reports import router as reports_router
from .settings import router as user_settings_router
from .templates import router as templates_router
from .users import router as users_router

router = Router(name="private_router")
router.include_router(common_router)
router.include_router(users_router)
router.include_router(chats_router)
router.include_router(reports_router)
router.include_router(templates_router)
router.include_router(categories_router)
router.include_router(user_settings_router)
