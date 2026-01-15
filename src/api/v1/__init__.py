from fastapi import APIRouter, Depends

from .routers import router as v1_router

router = APIRouter(
    prefix="/v1",
    # dependencies=[Depends(verify_service_jwt)],
)


router.include_router(v1_router)
