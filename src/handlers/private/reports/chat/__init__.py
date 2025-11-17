from aiogram import Router

from .chat_report_handler import router as chat_report_router

router = Router(name="chat_report_router")

router.include_router(chat_report_router)
