from datetime import datetime
from typing import Optional

import pytz

from config import settings


class TimeZoneService:
    DEFAULT_TIMEZONE = pytz.timezone(settings.TIMEZONE)

    @classmethod
    def convert_to_local_time(
        cls, dt: datetime, source_tz: Optional[pytz.BaseTzInfo] = None
    ) -> datetime:
        if dt.tzinfo is None:
            source_tz = pytz.utc
            dt = source_tz.localize(dt)
        elif source_tz is None:
            source_tz = dt.tzinfo

        # Конвертируем во временную зону по умолчанию
        return dt.astimezone(cls.DEFAULT_TIMEZONE)

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(cls.DEFAULT_TIMEZONE)

    @classmethod
    def format_time(cls, dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Форматирует дату-время в строку

        :param dt: Дата-время
        :param fmt: Формат вывода
        :return: Строка
        """
        return dt.strftime(fmt)
