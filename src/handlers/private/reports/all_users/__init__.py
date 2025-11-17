from aiogram import Router

from .all_users_report_handler import router as all_users_report_router
from .back_to_periods_handler import router as back_to_periods_router
from .back_to_user_actions_handler import (
    router as back_to_user_actions_router,
)

router = Router(name="all_users_report_router")

router.include_router(all_users_report_router)
router.include_router(back_to_periods_router)
router.include_router(back_to_user_actions_router)
