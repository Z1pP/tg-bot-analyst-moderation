from aiogram import Router

from .select_template import router as select_template_router

router = Router(name="templates_callbacks")
router.include_router(select_template_router)
