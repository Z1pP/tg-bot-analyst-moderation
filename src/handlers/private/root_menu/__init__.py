from aiogram import Router

from filters.root_dev_filter import RootDevOnlyFilter

from .admin_logs import router as admin_logs_router
from .navigation import router as navigation_router
from .release_notes import router as release_notes_router
from .roles_manager import router as roles_manager_router

router = Router(name="root_menu_router")
router.message.filter(RootDevOnlyFilter())
router.callback_query.filter(RootDevOnlyFilter())


router.include_router(navigation_router)
router.include_router(admin_logs_router)
router.include_router(release_notes_router)
router.include_router(roles_manager_router)
