"""
Эндпоинты аналитики для Mini App.

GET  /api/v1/miniapp/analytics/users          — отчёт по всем отслеживаемым пользователям
GET  /api/v1/miniapp/analytics/users/{user_id} — отчёт по одному пользователю
POST /api/v1/miniapp/analytics/tracking        — добавить пользователя в отслеживание
DELETE /api/v1/miniapp/analytics/tracking/{user_tgid} — удалить из отслеживания
"""

import json
import logging
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from punq import Container
from pydantic import BaseModel

from api.dependencies.miniapp import TelegramInitData
from constants.period import TimePeriod
from container import container as app_container
from dto.report import AllUsersReportDTO, SingleUserReportDTO
from dto.user_tracking import RemoveUserTrackingDTO, UserTrackingDTO
from usecases.report import GetAllUsersReportUseCase, GetSingleUserReportUseCase
from usecases.user_tracking import (
    AddUserToTrackingUseCase,
    RemoveUserFromTrackingUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_PERIODS = [p.value for p in TimePeriod if p != TimePeriod.CUSTOM]


def get_container() -> Container:
    return app_container


def _tg_id_from_init_data(init_data: dict) -> str:
    user_raw = init_data.get("user", "{}")
    try:
        user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        return str(user.get("id", "0"))
    except Exception:
        return "0"


def _username_from_init_data(init_data: dict) -> str:
    user_raw = init_data.get("user", "{}")
    try:
        user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        return user.get("username", "")
    except Exception:
        return ""


def _serialize_day_stats(s) -> Optional[dict]:
    if s is None:
        return None
    return {
        "first_message_time": s.first_message_time.strftime("%H:%M")
        if s.first_message_time
        else None,
        "first_reaction_time": s.first_reaction_time.strftime("%H:%M")
        if s.first_reaction_time
        else None,
        "last_message_time": s.last_message_time.strftime("%H:%M")
        if s.last_message_time
        else None,
        "avg_messages_per_hour": s.avg_messages_per_hour,
        "total_messages": s.total_messages,
        "warns_count": s.warns_count,
        "bans_count": s.bans_count,
    }


def _serialize_multi_day_stats(s) -> Optional[dict]:
    if s is None:
        return None
    return {
        "avg_first_message_time": s.avg_first_message_time,
        "avg_first_reaction_time": s.avg_first_reaction_time,
        "avg_last_message_time": s.avg_last_message_time,
        "avg_messages_per_hour": s.avg_messages_per_hour,
        "avg_messages_per_day": s.avg_messages_per_day,
        "total_messages": s.total_messages,
        "warns_count": s.warns_count,
        "bans_count": s.bans_count,
    }


def _serialize_replies_stats(s) -> dict:
    def fmt(sec):
        if sec is None:
            return None
        m, sec = divmod(sec, 60)
        return f"{m}м {sec}с" if m else f"{sec}с"

    return {
        "total_count": s.total_count,
        "min": fmt(s.min_time_seconds),
        "max": fmt(s.max_time_seconds),
        "avg": fmt(s.avg_time_seconds),
        "median": fmt(s.median_time_seconds),
    }


@router.get("/analytics/users")
async def get_all_users_report(
    init_data: TelegramInitData,
    period: str = Query(default="За сегодня"),
    dc: Container = Depends(get_container),
):
    """Отчёт по всем отслеживаемым пользователям за период."""
    tg_id = _tg_id_from_init_data(init_data)

    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Valid: {VALID_PERIODS}",
        )

    start_date, end_date = TimePeriod.to_datetime(period)

    uc = cast(GetAllUsersReportUseCase, dc.resolve(GetAllUsersReportUseCase))
    result = await uc.execute(
        AllUsersReportDTO(
            user_tg_id=tg_id,
            start_date=start_date,
            end_date=end_date,
            selected_period=period,
        )
    )

    if result.error_message:
        return {
            "error": result.error_message,
            "users": [],
            "period": period,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "is_single_day": result.is_single_day,
        }

    users_out = []
    for u in result.users_stats:
        users_out.append(
            {
                "user_id": u.user_id,
                "username": u.username,
                "day_stats": _serialize_day_stats(u.day_stats),
                "multi_day_stats": _serialize_multi_day_stats(u.multi_day_stats),
                "replies_stats": _serialize_replies_stats(u.replies_stats),
                "breaks": u.breaks,
            }
        )

    return {
        "users": users_out,
        "period": period,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "is_single_day": result.is_single_day,
        "error": None,
    }


@router.get("/analytics/users/{user_id}")
async def get_single_user_report(
    user_id: int,
    init_data: TelegramInitData,
    period: str = Query(default="За сегодня"),
    dc: Container = Depends(get_container),
):
    """Отчёт по одному пользователю за период."""
    tg_id = _tg_id_from_init_data(init_data)

    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Valid: {VALID_PERIODS}",
        )

    start_date, end_date = TimePeriod.to_datetime(period)

    uc = cast(GetSingleUserReportUseCase, dc.resolve(GetSingleUserReportUseCase))
    try:
        result = await uc.execute(
            SingleUserReportDTO(
                user_id=user_id,
                admin_tg_id=tg_id,
                start_date=start_date,
                end_date=end_date,
                selected_period=period,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "user_id": result.user_id,
        "username": result.username,
        "period": period,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "is_single_day": result.is_single_day,
        "day_stats": _serialize_day_stats(result.day_stats),
        "multi_day_stats": _serialize_multi_day_stats(result.multi_day_stats),
        "replies_stats": _serialize_replies_stats(result.replies_stats),
        "breaks": result.breaks,
        "error": result.error_message,
    }


class AddTrackingRequest(BaseModel):
    user_tgid: Optional[str] = None
    user_username: Optional[str] = None


@router.post("/analytics/tracking", status_code=status.HTTP_201_CREATED)
async def add_user_to_tracking(
    body: AddTrackingRequest,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Добавить пользователя в отслеживание."""
    tg_id = _tg_id_from_init_data(init_data)
    username = _username_from_init_data(init_data)

    if not body.user_tgid and not body.user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите user_tgid или user_username",
        )

    uc = cast(AddUserToTrackingUseCase, dc.resolve(AddUserToTrackingUseCase))
    result = await uc.execute(
        UserTrackingDTO(
            admin_tgid=tg_id,
            admin_username=username,
            user_tgid=body.user_tgid,
            user_username=body.user_username,
        )
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message or "Не удалось добавить пользователя",
        )

    return {"ok": True, "user_id": result.user_id, "message": result.message}


@router.delete("/analytics/tracking/{user_tgid}")
async def remove_user_from_tracking(
    user_tgid: str,
    init_data: TelegramInitData,
    dc: Container = Depends(get_container),
):
    """Удалить пользователя из отслеживания."""
    tg_id = _tg_id_from_init_data(init_data)
    username = _username_from_init_data(init_data)

    uc = cast(RemoveUserFromTrackingUseCase, dc.resolve(RemoveUserFromTrackingUseCase))
    ok = await uc.execute(
        RemoveUserTrackingDTO(
            admin_tgid=tg_id,
            admin_username=username,
            user_tgid=user_tgid,
        )
    )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден или не в отслеживании",
        )

    return {"ok": True}
