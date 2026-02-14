from aiogram import Router

from .navigarion import router as navigation_router

router = Router(name="release_notes_router")
router.include_router(navigation_router)
