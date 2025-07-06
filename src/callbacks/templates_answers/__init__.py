from aiogram import Router

from .delete_template import router as delete_template_router
from .select_template import router as select_template_router

router = Router(name="templates_callbacks")
router.include_router(select_template_router)
router.include_router(delete_template_router)
