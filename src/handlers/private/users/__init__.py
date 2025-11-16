from aiogram import Router

from .add_user_to_tracking import router as add_router
from .back_to_users_menu import router as back_router
from .delete_user_from_tracking import router as delete_router
from .list_tracked_users import router as list_router
from .pagination import router as pagination_router
from .users_menu import router as menu_router

router = Router(name="users_router")
router.include_router(menu_router)
router.include_router(back_router)
router.include_router(list_router)
router.include_router(add_router)
router.include_router(delete_router)
router.include_router(pagination_router)
