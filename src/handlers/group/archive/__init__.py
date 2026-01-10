from aiogram import Router

from .bind import router as bind_router

router = Router(name=__name__)
router.include_router(bind_router)
