from aiogram import Router

from .add import router as add_router
from .delete import router as delete_router
from .list import router as list_router
from .management import router as management_router
from .menu import router as menu_router
from .pagination import router as pagination_router
from .select_all_users import router as select_all_router
from .select_specific_user import router as select_specific_router

router = Router(name="users_router")

router.include_router(menu_router)
router.include_router(list_router)
router.include_router(add_router)
router.include_router(delete_router)
router.include_router(pagination_router)
router.include_router(select_all_router)
router.include_router(select_specific_router)
router.include_router(management_router)
