from aiogram import Router

from .add_note import router as add_note_router
from .broadcast_note import router as broadcast_note_router
from .delete_note import router as delete_note_router
from .edit_note import router as edit_note_router
from .navigarion import router as navigation_router
from .pagination import router as pagination_router
from .view_note import router as view_note_router

router = Router(name="release_notes_router")
router.include_router(navigation_router)
router.include_router(pagination_router)
router.include_router(add_note_router)
router.include_router(view_note_router)
router.include_router(edit_note_router)
router.include_router(delete_note_router)
router.include_router(broadcast_note_router)
