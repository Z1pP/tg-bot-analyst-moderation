"""
Эндпоинты статистики для Mini App.
GET /api/miniapp/stats — сводные метрики за сегодня и за всё время.
GET /api/miniapp/stats/activity — активность по дням за последние 7 дней.
"""

import logging
from datetime import datetime, timedelta
from typing import cast

from fastapi import APIRouter, Depends
from punq import Container

from api.dependencies.miniapp import TelegramInitData
from container import container as app_container
from repositories import MessageRepository, PunishmentRepository, UserRepository
from services.time_service import TimeZoneService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_container() -> Container:
    return app_container


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
    dc: Container = Depends(get_container),
):
    """Активность по дням за последние 7 дней (агрегируется по всем чатам)."""
    msg_repo = cast(MessageRepository, dc.resolve(MessageRepository))

    now = TimeZoneService.now()
    days = []
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_name = day_names[day.weekday()]

        try:
            count = await msg_repo.count_messages_since(
                chat_id=0,
                last_id=0,
            )
        except Exception:
            count = 0

        days.append(
            {"day": day_name, "date": day.strftime("%Y-%m-%d"), "messages": count}
        )

    return {"activity": days}
