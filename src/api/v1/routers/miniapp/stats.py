"""
Эндпоинты статистики для Mini App.
GET /api/miniapp/stats             — сводные метрики за сегодня и за всё время.
GET /api/miniapp/stats/activity    — активность по дням (messages + warns + bans).
GET /api/miniapp/stats/moderators  — разбивка наказаний по модераторам за период.
"""

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from punq import Container

from api.dependencies.container import get_container
from api.dependencies.miniapp import TelegramInitData
from constants.period import TimePeriod
from usecases.stats import (
    GetActivityStatsUseCase,
    GetModeratorsStatsUseCase,
    GetStatsSummaryUseCase,
)

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_PERIODS = [p.value for p in TimePeriod if p != TimePeriod.CUSTOM]


@router.get("/stats")
async def get_stats(
    _: TelegramInitData,
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    usecase = cast(GetStatsSummaryUseCase, dc.resolve(GetStatsSummaryUseCase))
    result = await usecase.execute()
    return result.model_dump()


@router.get("/stats/activity")
async def get_activity(
    _: TelegramInitData,
    days_count: int = Query(default=7, ge=7, le=30, alias="days"),
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    """
    Активность по дням: количество сообщений, варнов и банов за каждый день.
    Параметр days: глубина в днях (от 7 до 30, по умолчанию 7).
    """
    usecase = cast(GetActivityStatsUseCase, dc.resolve(GetActivityStatsUseCase))
    result = await usecase.execute(days_count=days_count)
    return result.model_dump()


@router.get("/stats/moderators")
async def get_moderators_stats(
    _: TelegramInitData,
    period: str = Query(default="За сегодня"),
    dc: Container = Depends(get_container),
) -> dict[str, Any]:
    """
    Разбивка наказаний (варны + баны) по каждому модератору за выбранный период.
    Используется для pie chart / bar chart «кто сколько сделал».
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Valid: {VALID_PERIODS}",
        )

    start_date, end_date = TimePeriod.to_datetime(period)
    usecase = cast(GetModeratorsStatsUseCase, dc.resolve(GetModeratorsStatsUseCase))
    result = await usecase.execute(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )
    return result.model_dump()