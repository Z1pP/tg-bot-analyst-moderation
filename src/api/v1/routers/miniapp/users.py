"""
Эндпоинты пользователей для Mini App.
GET /api/miniapp/users           — список отслеживаемых пользователей
GET /api/miniapp/users/me        — профиль текущего пользователя
"""

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from punq import Container

from api.dependencies.container import get_container
from api.dependencies.miniapp import TelegramInitData, tg_id_from_init_data
from dto.user import UserDTO
from usecases.user import GetUserByTgIdUseCase
from usecases.user_tracking import GetListTrackedUsersUseCase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users/me")
async def get_me(
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    tg_id = tg_id_from_init_data(init_data)
    get_user = cast(GetUserByTgIdUseCase, dc.resolve(GetUserByTgIdUseCase))

    user = await get_user.execute(tg_id=tg_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered in the system",
        )

    return UserDTO.from_model(user).model_dump()


@router.get("/users")
async def get_users(
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    tg_id = tg_id_from_init_data(init_data)
    get_user = cast(GetUserByTgIdUseCase, dc.resolve(GetUserByTgIdUseCase))
    get_tracked = cast(
        GetListTrackedUsersUseCase, dc.resolve(GetListTrackedUsersUseCase)
    )

    caller = await get_user.execute(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tracked = await get_tracked.execute(admin_tgid=tg_id)

    return {
        "users": [u.model_dump() for u in tracked],
        "total": len(tracked),
    }