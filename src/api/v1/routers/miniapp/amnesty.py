"""
Эндпоинты амнистии для Mini App.

GET  /api/v1/miniapp/amnesty/chats/{user_tgid} — чаты, где у пользователя есть ограничения
POST /api/v1/miniapp/amnesty/unban             — снять бан
POST /api/v1/miniapp/amnesty/unmute            — снять мьют
POST /api/v1/miniapp/amnesty/cancel_warn       — отменить последний варн
"""

import logging
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from punq import Container
from pydantic import BaseModel

from api.dependencies.container import get_container
from api.dependencies.miniapp import (
    TelegramInitData,
    tg_id_from_init_data,
    username_from_init_data,
)
from dto.amnesty import AmnestyUserDTO
from dto.chat_dto import ChatDTO
from exceptions.base import BotBaseException
from repositories import UserRepository
from repositories.chat_repository import ChatRepository
from usecases.amnesty import (
    CancelLastWarnUseCase,
    GetChatsWithAnyRestrictionUseCase,
    UnbanUserUseCase,
    UnmuteUserUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_violator_and_chats(
    violator_tgid: str,
    chat_ids: List[int],
    admin_tgid: str,
    admin_username: str,
    dc: Container,
) -> AmnestyUserDTO:
    """
    Получает данные нарушителя и чатов из БД,
    формирует AmnestyUserDTO для use cases амнистии.
    """
    user_repo = cast(UserRepository, dc.resolve(UserRepository))
    chat_repo = cast(ChatRepository, dc.resolve(ChatRepository))

    violator = await user_repo.get_user_by_tg_id(tg_id=violator_tgid)
    if not violator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с tg_id={violator_tgid} не найден",
        )

    chat_dtos: List[ChatDTO] = []
    for chat_id in chat_ids:
        chat = await chat_repo.get_chat_by_id(chat_id=chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Чат с id={chat_id} не найден",
            )
        chat_dtos.append(ChatDTO.from_model(chat))

    return AmnestyUserDTO(
        violator_tgid=violator_tgid,
        violator_username=violator.username or "",
        violator_id=violator.id,
        admin_tgid=admin_tgid,
        admin_username=admin_username,
        chat_dtos=chat_dtos,
    )


@router.get("/amnesty/chats/{user_tgid}")
async def get_chats_with_restrictions(
    user_tgid: str,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Возвращает чаты, где у пользователя есть ограничения (бан, мут, варны)."""
    admin_tgid = tg_id_from_init_data(init_data)
    admin_username = username_from_init_data(init_data)

    user_repo = cast(UserRepository, dc.resolve(UserRepository))
    violator = await user_repo.get_user_by_tg_id(tg_id=user_tgid)
    if not violator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с tg_id={user_tgid} не найден",
        )

    dto = AmnestyUserDTO(
        violator_tgid=user_tgid,
        violator_username=violator.username or "",
        violator_id=violator.id,
        admin_tgid=admin_tgid,
        admin_username=admin_username,
    )

    uc = cast(
        GetChatsWithAnyRestrictionUseCase, dc.resolve(GetChatsWithAnyRestrictionUseCase)
    )
    chats = await uc.execute(dto=dto)

    if chats is None:
        return {"chats": [], "total": 0}

    return {
        "chats": [c.model_dump() for c in chats],
        "total": len(chats),
    }


class AmnestyRequest(BaseModel):
    violator_tgid: str
    chat_ids: List[int]


class CancelWarnRequest(BaseModel):
    violator_tgid: str
    chat_id: int


@router.post("/amnesty/unban", status_code=status.HTTP_200_OK)
async def unban_user(
    body: AmnestyRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Снимает бан с пользователя в указанных чатах."""
    admin_tgid = tg_id_from_init_data(init_data)
    admin_username = username_from_init_data(init_data)

    dto = await _resolve_violator_and_chats(
        violator_tgid=body.violator_tgid,
        chat_ids=body.chat_ids,
        admin_tgid=admin_tgid,
        admin_username=admin_username,
        dc=dc,
    )

    uc = cast(UnbanUserUseCase, dc.resolve(UnbanUserUseCase))
    try:
        await uc.execute(dto=dto)
    except BotBaseException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.get_user_message(),
        )

    return {"ok": True}


@router.post("/amnesty/unmute", status_code=status.HTTP_200_OK)
async def unmute_user(
    body: AmnestyRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Снимает мьют с пользователя в указанных чатах."""
    admin_tgid = tg_id_from_init_data(init_data)
    admin_username = username_from_init_data(init_data)

    dto = await _resolve_violator_and_chats(
        violator_tgid=body.violator_tgid,
        chat_ids=body.chat_ids,
        admin_tgid=admin_tgid,
        admin_username=admin_username,
        dc=dc,
    )

    uc = cast(UnmuteUserUseCase, dc.resolve(UnmuteUserUseCase))
    try:
        await uc.execute(dto=dto)
    except BotBaseException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.get_user_message(),
        )

    return {"ok": True}


@router.post("/amnesty/cancel_warn", status_code=status.HTTP_200_OK)
async def cancel_last_warn(
    body: CancelWarnRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Отменяет последнее предупреждение пользователя в указанном чате."""
    admin_tgid = tg_id_from_init_data(init_data)
    admin_username = username_from_init_data(init_data)

    dto = await _resolve_violator_and_chats(
        violator_tgid=body.violator_tgid,
        chat_ids=[body.chat_id],
        admin_tgid=admin_tgid,
        admin_username=admin_username,
        dc=dc,
    )

    uc = cast(CancelLastWarnUseCase, dc.resolve(CancelLastWarnUseCase))
    try:
        result = await uc.execute(dto=dto)
    except BotBaseException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.get_user_message(),
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предупреждений для отмены не найдено",
        )

    return {
        "ok": True,
        "current_warns_count": result.current_warns_count,
        "next_punishment_type": result.next_punishment_type,
        "next_punishment_duration": result.next_punishment_duration,
    }
