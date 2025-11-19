from aiogram import Router

from .role_handler import router as role_router

router = Router(name="roles_router")
router.include_router(role_router)
