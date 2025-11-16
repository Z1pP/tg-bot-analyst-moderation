from aiogram import Router

from .all_users_report import router as all_users_report_router
from .back_handler import router as back_router
from .calendar_callback_handler import router as calendar_router
from .detailed_report import router as detailed_report_router
from .single_chat_report import router as chat_report_router
from .single_user_report import router as single_user_report_router

router = Router(name="report_router")
router.include_router(back_router)
router.include_router(calendar_router)
router.include_router(chat_report_router)
router.include_router(all_users_report_router)
router.include_router(single_user_report_router)
router.include_router(detailed_report_router)
