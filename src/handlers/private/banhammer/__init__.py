from aiogram import Router


from .amnesty import router as amnesty_router
from .lock_menu import router as lock_menu_router
from .block_user import router as block_user_router
from .warn_user import router as warn_user_router
from .back_to_block_menu import router as back_to_block_menu_router

router = Router(name="banhammer_router")

router.include_router(back_to_block_menu_router)
router.include_router(lock_menu_router)
router.include_router(amnesty_router)
router.include_router(block_user_router)
router.include_router(warn_user_router)
