from aiogram import Router

from .add_moderator import router as add_router
from .delete_moderator import router as delete_router
from .list_handler import router as list_router

router = Router(name="moderators_router")
router.include_router(list_router)
router.include_router(add_router)
router.include_router(delete_router)
