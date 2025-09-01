from aiogram import Router

from .add_template import router as add_template_router
from .edit_template import router as edit_template_router
from .list_templates import router as list_templates_router
from .templates_menu import router as templates_menu_router

router = Router(name="answer_templates_router")
router.include_router(templates_menu_router)
router.include_router(add_template_router)
router.include_router(list_templates_router)
router.include_router(edit_template_router)
