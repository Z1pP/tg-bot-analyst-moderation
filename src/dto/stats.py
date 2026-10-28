"""DTO для статистики Mini App."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class StatsSummaryDTO(BaseModel):
    """Сводные метрики модерации."""

    active_users: int
    moderation_actions: int
    today_actions: int

    model_config = ConfigDict(frozen=True)


class ActivityDayDTO(BaseModel):
    """Активность за один день."""

    day: str
    date: str
    messages: int
    warns: int
    bans: int

    model_config = ConfigDict(frozen=True)


class ActivityStatsDTO(BaseModel):
    """Активность по дням."""

    activity: list[ActivityDayDTO]
    days: int

    model_config = ConfigDict(frozen=True)


class ModeratorStatsDTO(BaseModel):
    """Разбивка наказаний по одному модератору."""

    username: str
    tg_id: Optional[str] = None
    warns: int
    bans: int
    total: int

    model_config = ConfigDict(frozen=True)


class ModeratorsStatsDTO(BaseModel):
    """Разбивка наказаний по модераторам за период."""

    moderators: list[ModeratorStatsDTO]
    period: str

    model_config = ConfigDict(frozen=True)