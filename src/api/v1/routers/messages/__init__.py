from fastapi import APIRouter

from .create import router as create_router

router = APIRouter(prefix="/messages", tags=["messages"])
router.include_router(create_router)
