from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    chat_id: int
    admin_tg_id: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None
