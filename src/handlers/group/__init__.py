from aiogram import Router

from .message_handler import router as message_router

router = Router(name="group_router")
router.include_router(message_router)
