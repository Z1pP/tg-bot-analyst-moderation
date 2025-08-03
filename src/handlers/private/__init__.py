from aiogram import Router

from .categories import router as categories_router
from .chats import router as chats_router
from .common import router as common_router
from .moderators import router as moderators_router
from .reports import router as reports_router
from .templates import router as templates_router

router = Router(name="private_router")
router.include_router(common_router)
router.include_router(moderators_router)
router.include_router(chats_router)
router.include_router(reports_router)
router.include_router(templates_router)
router.include_router(categories_router)
