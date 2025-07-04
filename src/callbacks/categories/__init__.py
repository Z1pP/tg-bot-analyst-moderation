from aiogram import Router

from .select_category import router as select_category_router

router = Router(name="categories_callbacks")
router.include_router(select_category_router)
