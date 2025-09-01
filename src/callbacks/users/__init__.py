from aiogram import Router

from .pagination import router as pagination_router
from .select_all_moderators import router as all_users_router
from .select_specific_moderator import router as user_router

router = Router(name="users_callbacks")
router.include_router(all_users_router)
router.include_router(user_router)
router.include_router(pagination_router)
