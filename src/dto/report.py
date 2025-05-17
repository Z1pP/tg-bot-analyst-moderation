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
