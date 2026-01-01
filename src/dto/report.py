from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DailyReportDTO(BaseModel):
    username: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


class AVGReportDTO(BaseModel):
    username: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


class SingleUserReportDTO(BaseModel):
    user_id: int
    admin_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


class AllUsersReportDTO(BaseModel):
    user_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


class ChatReportDTO(BaseModel):
    chat_id: int  # Database id
    admin_tg_id: str  # Telegram id
    selected_period: str
    start_date: Optional[datetime] = None  # Для кастомных дат из календаря
    end_date: Optional[datetime] = None  # Для кастомных дат из календаря
    chat_tgid: Optional[str] = None  # Telegram id чата


class UserDayStats(BaseModel):
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime]
    first_reaction_time: Optional[datetime]
    avg_messages_per_hour: float
    total_messages: int

    model_config = ConfigDict(frozen=True)


class UserMultiDayStats(BaseModel):
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str]  # "HH:MM"
    avg_first_reaction_time: Optional[str]
    avg_messages_per_hour: float
    avg_messages_per_day: float
    total_messages: int

    model_config = ConfigDict(frozen=True)


class RepliesStats(BaseModel):
    """Статистика ответов пользователя"""

    total_count: int
    min_time_seconds: Optional[int]
    max_time_seconds: Optional[int]
    avg_time_seconds: Optional[int]
    median_time_seconds: Optional[int]

    model_config = ConfigDict(frozen=True)


class UserStatsDTO(BaseModel):
    """Статистика одного пользователя"""

    user_id: int
    username: str
    day_stats: Optional[UserDayStats]  # для однодневного отчета
    multi_day_stats: Optional[UserMultiDayStats]  # для многодневного
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные строки из BreakAnalysisService

    model_config = ConfigDict(frozen=True)


class SingleUserDayStats(BaseModel):
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime]
    first_reaction_time: Optional[datetime]
    avg_messages_per_hour: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0

    model_config = ConfigDict(frozen=True)


class SingleUserMultiDayStats(BaseModel):
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str]  # "HH:MM"
    avg_first_reaction_time: Optional[str]
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
    day_stats: Optional[SingleUserDayStats]
    multi_day_stats: Optional[SingleUserMultiDayStats]
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные из BreakAnalysisService
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class AllUsersUserStatsResult(BaseModel):
    """Статистика одного пользователя в отчете по всем пользователям"""

    user_id: int
    username: str
    day_stats: Optional[SingleUserDayStats]  # переиспользуем существующий
    multi_day_stats: Optional[SingleUserMultiDayStats]  # переиспользуем существующий
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
