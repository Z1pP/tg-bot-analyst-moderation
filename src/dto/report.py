from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DailyReportDTO:
    username: str
    start_date: datetime
    end_date: datetime


@dataclass
class AVGReportDTO:
    username: str
    time: timedelta


@dataclass
class ResponseTimeReportDTO:
    username: str
    days: int = 7  # По умолчанию отчет за неделю
