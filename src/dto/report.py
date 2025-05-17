from dataclasses import dataclass
from datetime import datetime


@dataclass
class DailyReportDTO:
    username: str
    start_date: datetime
    end_date: datetime
