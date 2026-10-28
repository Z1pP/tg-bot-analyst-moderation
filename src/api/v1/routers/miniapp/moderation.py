"""
Эндпоинты модерации для Mini App.
GET  /api/miniapp/moderation/log     — история действий (пагинация)
POST /api/miniapp/moderation/warn    — выдать предупреждение
POST /api/miniapp/moderation/ban     — заблокировать пользователя
"""

import logging
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from punq import Container
from pydantic import BaseModel

from api.dependencies.container import get_container
from api.dependencies.miniapp import (
    TelegramInitData,
    tg_id_from_init_data,
    username_from_init_data,
)
from constants.punishment import PunishmentActions as Actions
from dto.admin_log import GetAdminLogsPageDTO
from dto.chat_dto import GetChatWithArchiveDTO
from dto.moderation import ModerationActionDTO
from exceptions.base import BotBaseException
from usecases.admin_logs import GetModerationLogsUseCase
from usecases.chat import GetChatWithArchiveUseCase
from usecases.user import GetUserByTgIdUseCase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/moderation/log")
async def get_moderation_log(
    init_data: TelegramInitData,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    tg_id = tg_id_from_init_data(init_data)
    get_user = cast(GetUserByTgIdUseCase, dc.resolve(GetUserByTgIdUseCase))
    get_logs = cast(GetModerationLogsUseCase, dc.resolve(GetModerationLogsUseCase))

    caller = await get_user.execute(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result = await get_logs.execute(GetAdminLogsPageDTO(page=page, limit=limit))
    return result.model_dump(mode="json")


class ModerationActionRequest(BaseModel):
    action: str
    violator_username: str = ""
    violator_tgid: str
    chat_tgid: str
    reason: Optional[str] = None


@router.post("/moderation/action")
async def perform_moderation_action(
    body: ModerationActionRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    tg_id = tg_id_from_init_data(init_data)
    username = username_from_init_data(init_data)

    get_user = cast(GetUserByTgIdUseCase, dc.resolve(GetUserByTgIdUseCase))
    get_chat = cast(GetChatWithArchiveUseCase, dc.resolve(GetChatWithArchiveUseCase))

    caller = await get_user.execute(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    chat = await get_chat.execute(GetChatWithArchiveDTO(chat_tgid=body.chat_tgid))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )

    try:
        action = Actions(body.action)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action '{body.action}'. Valid: warning, ban",
        )

    from usecases.moderation import GiveUserBanUseCase, GiveUserWarnUseCase

    usecase_cls = (
        GiveUserWarnUseCase if action == Actions.WARNING else GiveUserBanUseCase
    )
    uc = dc.resolve(usecase_cls)

    dto = ModerationActionDTO(
        action=action,
        violator_tgid=body.violator_tgid,
        violator_username=body.violator_username,
        admin_tgid=tg_id,
        admin_username=username,
        chat_tgid=body.chat_tgid,
        chat_title=chat.title or "",
        reason=body.reason,
        from_admin_panel=True,
    )

    try:
        await uc.execute(dto)
    except BotBaseException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.get_user_message(),
        )

    return {"ok": True}
