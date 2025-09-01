from aiogram import Router

from .all_users_report import router as all_users_report_router
from .single_chat_report import router as chat_report_router
from .single_user_report import router as single_user_report_router

router = Router(name="report_router")
router.include_router(chat_report_router)
router.include_router(all_users_report_router)
router.include_router(single_user_report_router)
