from aiogram import Router

from .ban import router as ban_user_router
from .cancel import router as cancel_router

router = Router(name="automoderation_router")

router.include_router(ban_user_router)
router.include_router(cancel_router)
