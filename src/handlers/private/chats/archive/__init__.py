from aiogram import Router

from .archive import router as archive_router
from .change_sending_time import router as change_sending_time_router

router = Router(name=__name__)

router.include_router(archive_router)
router.include_router(change_sending_time_router)
