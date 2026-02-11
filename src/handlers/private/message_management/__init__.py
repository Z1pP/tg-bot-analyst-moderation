from aiogram import Router

from .actions import router as actions_router
from .delete import router as delete_router
from .link import router as link_router
from .menu import router as menu_router
from .pagination import router as pagination_router
from .reply import router as reply_router
from .send import router as send_router

router = Router()

router.include_router(menu_router)
router.include_router(link_router)
router.include_router(actions_router)
router.include_router(delete_router)
router.include_router(reply_router)
router.include_router(send_router)
router.include_router(pagination_router)

__all__ = ["router"]
