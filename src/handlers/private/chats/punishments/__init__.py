from aiogram import Router

from .create import router as create_punishment_router
from .set_default import router as set_default_punishment_router
from .settings import router as punishment_settings_router

router = Router(name="punishments_router")


router.include_router(punishment_settings_router)
router.include_router(set_default_punishment_router)
router.include_router(create_punishment_router)
