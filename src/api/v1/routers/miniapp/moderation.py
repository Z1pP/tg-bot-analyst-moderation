"""
Эндпоинты модерации для Mini App.
GET  /api/miniapp/moderation/log     — история действий (пагинация)
POST /api/miniapp/moderation/warn    — выдать предупреждение
POST /api/miniapp/moderation/ban     — заблокировать пользователя
"""

import logging
from typing import Optional, cast

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
from dto.moderation import ModerationActionDTO
from exceptions.base import BotBaseException
from repositories import AdminActionLogRepository, UserRepository
from repositories.chat_repository import ChatRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/moderation/log")
async def get_moderation_log(
    init_data: TelegramInitData,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    dc: Container = Depends(get_container),
):
    tg_id = tg_id_from_init_data(init_data)
    user_repo = cast(UserRepository, dc.resolve(UserRepository))
    log_repo = cast(AdminActionLogRepository, dc.resolve(AdminActionLogRepository))

    caller = await user_repo.get_user_by_tg_id(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    logs, total = await log_repo.get_logs_paginated(page=page, limit=limit)

    items = []
    for log in logs:
        items.append(
            {
                "id": log.id,
                "action_type": log.action_type,
                "details": log.details,
                "admin_username": log.admin.username if log.admin else None,
                "admin_tg_id": log.admin.tg_id if log.admin else None,
                "created_at": log.created_at.isoformat(),
            }
        )

    return {"items": items, "total": total, "page": page, "limit": limit}


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
):
    tg_id = tg_id_from_init_data(init_data)
    username = username_from_init_data(init_data)

    user_repo = cast(UserRepository, dc.resolve(UserRepository))
    chat_repo = cast(ChatRepository, dc.resolve(ChatRepository))

    caller = await user_repo.get_user_by_tg_id(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    chat = await chat_repo.get_chat_by_tg_id(chat_tg_id=body.chat_tgid)
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
