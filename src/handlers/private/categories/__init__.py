from aiogram import Router

from .add_category import router as add_category_router
from .list_categories import router as list_categories_router

router = Router(name="answer_category_router")
router.include_router(add_category_router)
router.include_router(list_categories_router)
