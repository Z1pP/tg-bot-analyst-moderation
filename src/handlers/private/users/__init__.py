from aiogram import Router

from .add_user import router as add_router
from .delete_user import router as delete_router
from .list_users import router as list_router

router = Router(name="users_router")
router.include_router(list_router)
router.include_router(add_router)
router.include_router(delete_router)
