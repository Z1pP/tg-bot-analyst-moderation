from aiogram import Router

from .delete_template import router as delete_template_router
from .edit_template import router as edit_template_router
from .pagination import router as pagination_router
from .select_scope import router as select_scope_router
from .select_template import router as select_template_router

router = Router(name="templates_callback")
router.include_router(pagination_router)
router.include_router(select_scope_router)
router.include_router(select_template_router)
router.include_router(delete_template_router)
router.include_router(edit_template_router)
