from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SingleUserReportDTO(BaseModel):
    user_id: int
    admin_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class AllUsersReportDTO(BaseModel):
    user_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ChatReportDTO(BaseModel):
    chat_id: int  # Database id
    admin_tg_id: str  # Telegram id
    selected_period: str
    start_date: Optional[datetime] = None  # Для кастомных дат из календаря
    end_date: Optional[datetime] = None  # Для кастомных дат из календаря
    chat_tgid: Optional[str] = None  # Telegram id чата

    model_config = ConfigDict(frozen=True)


class UserDayStats(BaseModel):
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime] = None
    first_reaction_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    avg_messages_per_hour: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0

    model_config = ConfigDict(frozen=True)


class UserMultiDayStats(BaseModel):
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str] = None  # "HH:MM"
    avg_first_reaction_time: Optional[str] = None
    avg_last_message_time: Optional[str] = None
    avg_messages_per_hour: float
    avg_messages_per_day: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0

    model_config = ConfigDict(frozen=True)


class RepliesStats(BaseModel):
    """Статистика ответов пользователя"""

    total_count: int
    min_time_seconds: Optional[int] = None
    max_time_seconds: Optional[int] = None
    avg_time_seconds: Optional[int] = None
    median_time_seconds: Optional[int] = None

    model_config = ConfigDict(frozen=True)


class BreakIntervalDTO(BaseModel):
    """Интервал перерыва в пределах дня."""

    start_time: str
    end_time: str
    duration_minutes: int

    model_config = ConfigDict(frozen=True)


class BreakDayDTO(BaseModel):
    """Перерывы за один день."""

    date: datetime
    total_break_seconds: int
    intervals: List[BreakIntervalDTO]

    model_config = ConfigDict(frozen=True)


class BreaksDetailUserDTO(BaseModel):
    """Детализация перерывов одного пользователя."""

    username: str
    has_activity: bool
    days: List[BreakDayDTO]

    model_config = ConfigDict(frozen=True)


class BreaksDetailReportDTO(BaseModel):
    """Результат детализации перерывов."""

    period: str
    users: List[BreaksDetailUserDTO]
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class UserStatsDTO(BaseModel):
    """Статистика одного пользователя"""

    user_id: int
    username: str
    day_stats: Optional[UserDayStats] = None  # для однодневного отчета
    multi_day_stats: Optional[UserMultiDayStats] = None  # для многодневного
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные строки из BreakAnalysisService
    total_break_time: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class SingleUserDayStats(BaseModel):
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime] = None
    first_reaction_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    avg_messages_per_hour: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0

    model_config = ConfigDict(frozen=True)


class SingleUserMultiDayStats(BaseModel):
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str] = None  # "HH:MM"
    avg_first_reaction_time: Optional[str] = None
    avg_last_message_time: Optional[str] = None
    avg_messages_per_hour: float
    avg_messages_per_day: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0

    model_config = ConfigDict(frozen=True)


class SingleUserReportResultDTO(BaseModel):
    """Результат UseCase с сырыми данными отчета по пользователю"""

    username: str
    user_id: int
    start_date: datetime
    end_date: datetime
    is_single_day: bool
    day_stats: Optional[SingleUserDayStats] = None
    multi_day_stats: Optional[SingleUserMultiDayStats] = None
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные из BreakAnalysisService
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class AllUsersUserStatsResult(BaseModel):
    """Статистика одного пользователя в отчете по всем пользователям"""

    user_id: int
    username: str
    day_stats: Optional[SingleUserDayStats] = None  # переиспользуем существующий
    multi_day_stats: Optional[SingleUserMultiDayStats] = None  # переиспользуем существующий
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные из BreakAnalysisService

    model_config = ConfigDict(frozen=True)


class AllUsersReportResultDTO(BaseModel):
    """Результат UseCase с сырыми данными отчета по всем пользователям"""

    start_date: datetime
    end_date: datetime
    is_single_day: bool
    users_stats: List[AllUsersUserStatsResult]
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ReportResultDTO(BaseModel):
    """Результат UseCase с сырыми данными отчета"""

    users_stats: List[UserStatsDTO]
    chat_title: str
    start_date: datetime
    end_date: datetime
    is_single_day: bool
    working_hours: float
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)
