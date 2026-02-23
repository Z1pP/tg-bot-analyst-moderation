"""
Эндпоинты статистики для Mini App.
GET /api/miniapp/stats             — сводные метрики за сегодня и за всё время.
GET /api/miniapp/stats/activity    — активность по дням (messages + warns + bans).
GET /api/miniapp/stats/moderators  — разбивка наказаний по модераторам за период.
"""

import logging
from datetime import datetime, timedelta
from typing import cast

from fastapi import APIRouter, Depends, Query
from punq import Container

from api.dependencies.container import get_container
from api.dependencies.miniapp import TelegramInitData
from constants.period import TimePeriod
from repositories import MessageRepository, PunishmentRepository, UserRepository
from services.time_service import TimeZoneService

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_PERIODS = [p.value for p in TimePeriod if p != TimePeriod.CUSTOM]


@router.get("/stats")
async def get_stats(
    _: TelegramInitData,
    dc: Container = Depends(get_container),
):
    punishment_repo = cast(PunishmentRepository, dc.resolve(PunishmentRepository))
    user_repo = cast(UserRepository, dc.resolve(UserRepository))

    now = TimeZoneService.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    moderators = await user_repo.get_all_moderators()
    total_users = len(moderators)

    today_actions = 0
    total_actions = 0
    for mod in moderators:
        counts_today = await punishment_repo.get_punishment_counts_by_moderator(
            moderator_id=mod.id,
            start_date=today_start,
            end_date=today_end,
        )
        counts_all = await punishment_repo.get_punishment_counts_by_moderator(
            moderator_id=mod.id,
            start_date=datetime(2000, 1, 1),
            end_date=today_end,
        )
        today_actions += counts_today.get("warns", 0) + counts_today.get("bans", 0)
        total_actions += counts_all.get("warns", 0) + counts_all.get("bans", 0)

    return {
        "active_users": total_users,
        "moderation_actions": total_actions,
        "today_actions": today_actions,
    }


@router.get("/stats/activity")
async def get_activity(
    _: TelegramInitData,
    days_count: int = Query(default=7, ge=7, le=30, alias="days"),
    dc: Container = Depends(get_container),
):
    """
    Активность по дням: количество сообщений, варнов и банов за каждый день.
    Параметр days: глубина в днях (от 7 до 30, по умолчанию 7).
    """
    msg_repo = cast(MessageRepository, dc.resolve(MessageRepository))
    punishment_repo = cast(PunishmentRepository, dc.resolve(PunishmentRepository))

    now = TimeZoneService.now()
    period_start = (now - timedelta(days=days_count - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    try:
        daily_punishments = await punishment_repo.get_daily_punishment_counts(
            start=period_start, end=period_end
        )
    except Exception:
        daily_punishments = {}

    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    result = []

    for i in range(days_count - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_str = day.strftime("%Y-%m-%d")

        try:
            messages = await msg_repo.count_messages_by_date_range(
                start=day_start,
                end=day_end,
            )
        except Exception:
            messages = 0

        punishments = daily_punishments.get(date_str, {"warns": 0, "bans": 0})

        result.append(
            {
                "day": day_names[day.weekday()],
                "date": date_str,
                "messages": messages,
                "warns": punishments["warns"],
                "bans": punishments["bans"],
            }
        )

    return {"activity": result, "days": days_count}


@router.get("/stats/moderators")
async def get_moderators_stats(
    _: TelegramInitData,
    period: str = Query(default="За сегодня"),
    dc: Container = Depends(get_container),
):
    """
    Разбивка наказаний (варны + баны) по каждому модератору за выбранный период.
    Используется для pie chart / bar chart «кто сколько сделал».
    """
    if period not in VALID_PERIODS:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Valid: {VALID_PERIODS}",
        )

    start_date, end_date = TimePeriod.to_datetime(period)

    punishment_repo = cast(PunishmentRepository, dc.resolve(PunishmentRepository))
    user_repo = cast(UserRepository, dc.resolve(UserRepository))

    moderators = await user_repo.get_all_moderators()
    if not moderators:
        return {"moderators": [], "period": period}

    moderator_ids = [m.id for m in moderators]
    counts_by_id = await punishment_repo.get_punishment_counts_by_moderators(
        moderator_ids=moderator_ids,
        start_date=start_date,
        end_date=end_date,
    )

    result = []
    for mod in moderators:
        counts = counts_by_id.get(mod.id, {"warns": 0, "bans": 0})
        warns = counts["warns"]
        bans = counts["bans"]
        result.append(
            {
                "username": mod.username or f"ID:{mod.tg_id}",
                "tg_id": mod.tg_id,
                "warns": warns,
                "bans": bans,
                "total": warns + bans,
            }
        )

    result.sort(key=lambda x: x["total"], reverse=True)

    return {"moderators": result, "period": period}
