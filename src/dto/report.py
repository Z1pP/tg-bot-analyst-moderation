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
class ResponseTimeReportDTO:
    user_id: int
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class AllUsersReportDTO:
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class ChatReportDTO:
    chat_id: int
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None
