import re
from datetime import datetime, timedelta

from utils.username_validator import validate_username


def parse_data(text: str) -> tuple[datetime, datetime] | None:
    date = []
    data_segments = text.split("-")
    for data in data_segments:
        day, mounth = data.split(".")
        if not day.isdigit() or not mounth.isdigit():
            return None
        if int(day) > 31 or int(mounth) > 12:
            return None
        date.append(datetime(year=2025, month=int(mounth), day=int(day)))
    if len(date) != 2:
        return None
    if date[0] > date[1]:
        return None
    return date[0], date[1]


def parse_time(text: str) -> timedelta | None:
    pattern = re.compile(r"^(\d+)([hdwm])$", re.IGNORECASE)
    match = pattern.match(text.strip())

    if not match:
        return None

    try:
        value, unit = match.group(1), match.group(2).lower()
        value_int = int(value)

        match unit:
            case "h":
                return timedelta(hours=value_int)
            case "d":
                return timedelta(days=value_int)
            case "w":
                return timedelta(weeks=value_int)
            case "m":
                return timedelta(days=value_int * 30)
            case _:
                return None
    except (ValueError, TypeError):
        return None


def parse_username(text: str) -> str:
    return validate_username(username=text)
