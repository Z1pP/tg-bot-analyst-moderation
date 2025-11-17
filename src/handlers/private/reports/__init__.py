from aiogram import Router

from .all_users import router as all_users_report_router
from .calendar_handler import router as calendar_router
from .chat import router as chat_report_router
from .detailed_report import router as detailed_report_router
from .single_user import router as single_user_report_router

router = Router(name="report_router")
router.include_router(calendar_router)
router.include_router(chat_report_router)
router.include_router(all_users_report_router)
router.include_router(single_user_report_router)
router.include_router(detailed_report_router)
