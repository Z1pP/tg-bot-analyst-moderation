"""
Эндпоинты чатов для Mini App.
GET  /api/miniapp/chats          — список чатов администратора
POST /api/miniapp/chats/antibot  — переключить антибот
"""

import json
import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from punq import Container
from pydantic import BaseModel

from api.dependencies.miniapp import TelegramInitData
from container import container as app_container
from dto.chat_dto import ChatDTO
from exceptions.user import UserNotFoundException
from usecases.chat import GetAllChatsUseCase, ToggleAntibotUseCase

router = APIRouter()
logger = logging.getLogger(__name__)


def get_container() -> Container:
    return app_container


def _tg_id_from_init_data(init_data: dict) -> str:
    user_raw = init_data.get("user", "{}")
    try:
        user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        return str(user.get("id", "0"))
    except Exception:
        return "0"


@router.get("/chats")
async def get_chats(
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    tg_id = _tg_id_from_init_data(init_data)
    uc = cast(GetAllChatsUseCase, dc.resolve(GetAllChatsUseCase))

    try:
        chats = await uc.execute(tg_id=tg_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or not authorized",
        )

    return {
        "chats": [ChatDTO.from_model(c).model_dump() for c in chats],
        "total": len(chats),
    }


class ToggleAntibotRequest(BaseModel):
    chat_id: int
    enabled: bool


@router.post("/chats/antibot")
async def toggle_antibot(
    body: ToggleAntibotRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    tg_id = _tg_id_from_init_data(init_data)
    uc = cast(ToggleAntibotUseCase, dc.resolve(ToggleAntibotUseCase))

    try:
        result = await uc.execute(chat_id=body.chat_id, admin_tg_id=tg_id)
    except Exception as e:
        logger.error("toggle_antibot error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"ok": True, "antibot_enabled": result}
