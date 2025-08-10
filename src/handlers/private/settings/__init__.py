from aiogram import Router

from .user_settings import router as user_settings_router

router = Router(name=__name__)
router.include_router(user_settings_router)
