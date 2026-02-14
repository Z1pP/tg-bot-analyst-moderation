from aiogram import Router

from .navigation import router as navigation_router

router = Router(name=__name__)


router.include_router(navigation_router)
