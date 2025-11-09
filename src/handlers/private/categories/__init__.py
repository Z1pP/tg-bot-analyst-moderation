from aiogram import Router

from .delete_category import router as delete_category_router
from .edit_category import router as edit_category_router
from .list_categories import router as list_categories_router
from .pagination import router as pagination_router
from .select_category import router as select_category_router

router = Router(name="categories_router")
router.include_router(select_category_router)
router.include_router(delete_category_router)
router.include_router(edit_category_router)
router.include_router(pagination_router)
router.include_router(list_categories_router)
