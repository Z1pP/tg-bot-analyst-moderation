from aiogram import Router

from .archive_channel_setting import router as archive_channel_setting_router

router = Router(name=__name__)

router.include_router(archive_channel_setting_router)
