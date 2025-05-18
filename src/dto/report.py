from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


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
    report_date: Optional[datetime.date] = None
