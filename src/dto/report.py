from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class DailyReportDTO:
    username: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class AVGReportDTO:
    username: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class SingleUserReportDTO:
    user_id: int
    admin_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class AllUsersReportDTO:
    user_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class ChatReportDTO:
    chat_id: int  # Database id
    admin_tg_id: str  # Telegram id
    selected_period: str
    start_date: Optional[datetime] = None  # Для кастомных дат из календаря
    end_date: Optional[datetime] = None  # Для кастомных дат из календаря


@dataclass(frozen=True)
class UserDayStats:
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime]
    first_reaction_time: Optional[datetime]
    avg_messages_per_hour: float
    total_messages: int


@dataclass(frozen=True)
class UserMultiDayStats:
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str]  # "HH:MM"
    avg_first_reaction_time: Optional[str]
    avg_messages_per_hour: float
    avg_messages_per_day: float
    total_messages: int


@dataclass(frozen=True)
class RepliesStats:
    """Статистика ответов пользователя"""

    total_count: int
    min_time_seconds: Optional[int]
    max_time_seconds: Optional[int]
    avg_time_seconds: Optional[int]
    median_time_seconds: Optional[int]


@dataclass(frozen=True)
class UserStatsDTO:
    """Статистика одного пользователя"""

    user_id: int
    username: str
    day_stats: Optional[UserDayStats]  # для однодневного отчета
    multi_day_stats: Optional[UserMultiDayStats]  # для многодневного
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные строки из BreakAnalysisService


@dataclass(frozen=True)
class SingleUserDayStats:
    """Статистика пользователя за один день"""

    first_message_time: Optional[datetime]
    first_reaction_time: Optional[datetime]
    avg_messages_per_hour: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0


@dataclass(frozen=True)
class SingleUserMultiDayStats:
    """Статистика пользователя за несколько дней"""

    avg_first_message_time: Optional[str]  # "HH:MM"
    avg_first_reaction_time: Optional[str]
    avg_messages_per_hour: float
    avg_messages_per_day: float
    total_messages: int
    warns_count: int = 0
    bans_count: int = 0


@dataclass(frozen=True)
class SingleUserReportResultDTO:
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


@dataclass(frozen=True)
class AllUsersUserStatsResult:
    """Статистика одного пользователя в отчете по всем пользователям"""

    user_id: int
    username: str
    day_stats: Optional[SingleUserDayStats]  # переиспользуем существующий
    multi_day_stats: Optional[SingleUserMultiDayStats]  # переиспользуем существующий
    replies_stats: RepliesStats
    breaks: List[str]  # уже отформатированные из BreakAnalysisService


@dataclass(frozen=True)
class AllUsersReportResultDTO:
    """Результат UseCase с сырыми данными отчета по всем пользователям"""

    start_date: datetime
    end_date: datetime
    is_single_day: bool
    users_stats: List[AllUsersUserStatsResult]
    error_message: Optional[str] = None


@dataclass(frozen=True)
class ReportResultDTO:
    """Результат UseCase с сырыми данными отчета"""

    users_stats: List[UserStatsDTO]
    chat_title: str
    start_date: datetime
    end_date: datetime
    is_single_day: bool
    working_hours: float
    error_message: Optional[str] = None
