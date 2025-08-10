from aiogram import Router

from .all_users_report import router as full_moderators_report_router
from .single_chat_report import router as chat_report_router
from .single_user_report import router as response_time_report_router

router = Router(name="report_router")
router.include_router(chat_report_router)
router.include_router(full_moderators_report_router)
router.include_router(response_time_report_router)
