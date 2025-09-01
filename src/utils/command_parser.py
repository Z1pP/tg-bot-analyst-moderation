import re
from datetime import datetime, timedelta
from typing import Tuple

from exceptions.date import IncorrectDateFormatError
from services.time_service import TimeZoneService
from utils.username_validator import parse_and_validate_username


def parse_date(custom_period: str) -> Tuple[datetime, datetime]:
    """
    Парсит пользовательский ввод периода и возвращает кортеж с начальной и конечной датами.
    """
    parts = custom_period.split()

    date_part = parts[0] if parts else ""

    # Проверяем формат даты
    if "-" not in date_part:
        raise IncorrectDateFormatError()

    # Разбираем период
    start_str, end_str = date_part.split("-")

    # Парсим начальную дату
    try:
        if "." not in start_str or len(start_str.split(".")) != 2:
            raise IncorrectDateFormatError()

        day, month = map(int, start_str.split("."))
        current_year = TimeZoneService.now().year
        # Добавляем часовой пояс к начальной дате
        start_date = datetime(
            current_year, month, day, tzinfo=TimeZoneService.DEFAULT_TIMEZONE
        )
    except (ValueError, IndexError):
        raise IncorrectDateFormatError()

    # Парсим конечную дату
    if end_str:
        try:
            if "." not in end_str or len(end_str.split(".")) != 2:
                raise IncorrectDateFormatError()

            day, month = map(int, end_str.split("."))
            current_year = TimeZoneService.now().year
            # Добавляем часовой пояс к конечной дате
            end_date = datetime(
                current_year,
                month,
                day,
                23,
                59,
                59,
                tzinfo=TimeZoneService.DEFAULT_TIMEZONE,
            )
        except (ValueError, IndexError):
            raise IncorrectDateFormatError()
    else:
        end_date = TimeZoneService.now()

    # Проверяем, что конечная дата не раньше начальной
    if end_date < start_date:
        raise IncorrectDateFormatError()

    return start_date, end_date


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
    return parse_and_validate_username(text=text)


def parse_days(text: str) -> int:
    try:
        days = int(text.strip())
        if 0 > days > 365:
            return None
        return days
    except (ValueError, TypeError):
        return None
