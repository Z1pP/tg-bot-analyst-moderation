"""Archive handlers package router."""

from aiogram import Router

from .bind import router as bind_router
from .change_sending_time import router as change_sending_time_router
from .navigation import router as navigation_router
from .settings import router as settings_router
from .toggle import router as toggle_router

router = Router(name=__name__)

router.include_router(settings_router)
router.include_router(toggle_router)
router.include_router(bind_router)
router.include_router(navigation_router)
router.include_router(change_sending_time_router)
