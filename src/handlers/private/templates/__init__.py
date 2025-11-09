from aiogram import Router

from .add_template import router as add_template_router
from .delete_template import router as delete_template_router
from .edit_template import router as edit_template_router
from .list_templates import router as list_templates_router
from .pagination import router as pagination_router
from .select_template import router as select_template_router
from .select_template_scope import router as select_scope_router
from .templates_menu import router as templates_menu_router

router = Router(name="templates_router")
router.include_router(templates_menu_router)
router.include_router(add_template_router)
router.include_router(list_templates_router)
router.include_router(edit_template_router)
router.include_router(delete_template_router)
router.include_router(pagination_router)
router.include_router(select_scope_router)
router.include_router(select_template_router)
