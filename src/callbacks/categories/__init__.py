from aiogram import Router

from .delete_category import router as delete_category_router
from .select_category import router as select_category_router

router = Router(name="categories_callbacks")
router.include_router(select_category_router)
router.include_router(delete_category_router)
