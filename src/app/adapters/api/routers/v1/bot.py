from fastapi import APIRouter, Depends, Request

from app.adapters.api.dependencies.auth import verify_service_jwt

router = APIRouter(prefix="/bot", dependencies=[Depends(verify_service_jwt)])


@router.get("/")
async def get_bot_info(request: Request):
    return {"message": "Bot info"}
