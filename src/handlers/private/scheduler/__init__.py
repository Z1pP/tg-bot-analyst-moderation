from aiogram import Router

from .send_daily_chat_reports import router as send_daily_chat_reports_router

router = Router(name="scheduler_router")

router.include_router(send_daily_chat_reports_router)
