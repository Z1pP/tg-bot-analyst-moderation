from aiogram import Router
from .message_manager import router as message_router

router = Router(name=__name__)
router.include_router(message_router)
