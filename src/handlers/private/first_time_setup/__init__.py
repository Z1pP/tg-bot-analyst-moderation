from aiogram import Router

from .entry import router as entry_router
from .navigation import router as navigation_router
from .user_added import router as user_added_router
from .work_hours import router as work_hours_router

router = Router(name="first_time_setup")

router.include_router(entry_router)
router.include_router(user_added_router)
router.include_router(work_hours_router)
router.include_router(navigation_router)
