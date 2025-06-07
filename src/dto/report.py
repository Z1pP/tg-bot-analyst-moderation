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
    username: str
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None


@dataclass
class AllModeratorReportDTO:
    start_date: datetime
    end_date: datetime
    selected_period: Optional[str] = None
