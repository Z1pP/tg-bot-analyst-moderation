from aiogram import Router

from .back_to_chat_actions_handler import router as back_to_chat_actions_router
from .back_to_periods_handler import router as back_to_periods_router
from .chat_report_handler import router as chat_report_router
from .chat_summary_handler import router as chat_summary_router

router = Router(name="chat_report_router")

router.include_router(chat_report_router)
router.include_router(chat_summary_router)
router.include_router(back_to_periods_router)
router.include_router(back_to_chat_actions_router)
