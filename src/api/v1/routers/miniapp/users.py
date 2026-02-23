"""
Эндпоинты пользователей для Mini App.
GET /api/miniapp/users           — список отслеживаемых пользователей
GET /api/miniapp/users/me        — профиль текущего пользователя
"""

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from punq import Container

from api.dependencies.container import get_container
from api.dependencies.miniapp import TelegramInitData, tg_id_from_init_data
from dto.user import UserDTO
from repositories import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users/me")
async def get_me(
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    tg_id = tg_id_from_init_data(init_data)
    user_repo = cast(UserRepository, dc.resolve(UserRepository))

    user = await user_repo.get_user_by_tg_id(tg_id=tg_id)
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
):
    tg_id = tg_id_from_init_data(init_data)
    user_repo = cast(UserRepository, dc.resolve(UserRepository))

    caller = await user_repo.get_user_by_tg_id(tg_id=tg_id)
    if not caller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    tracked = await user_repo.get_tracked_users_for_admin(admin_tg_id=tg_id)

    return {
        "users": [UserDTO.from_model(u).model_dump() for u in tracked],
        "total": len(tracked),
    }
