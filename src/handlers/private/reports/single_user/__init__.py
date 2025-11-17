from aiogram import Router

from .back_to_periods_handler import router as back_to_periods_router
from .back_to_user_actions_handler import router as back_to_user_actions_router
from .single_user_report_handler import router as single_user_report_router

router = Router(name="single_user_report_router")

router.include_router(single_user_report_router)
router.include_router(back_to_user_actions_router)
router.include_router(back_to_periods_router)
