from aiogram import Router

from .list_logs import router as list_logs_router
from .pagination import router as pagination_router

router = Router(name="admin_logs_router")

router.include_router(list_logs_router)
router.include_router(pagination_router)
