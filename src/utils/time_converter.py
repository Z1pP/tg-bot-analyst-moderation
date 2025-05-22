from datetime import datetime

import pytz


class TimeZoneService:
    """
    Класс для работа со временем
    """

    # Константа для часового пояса UTC+3
    MOSCOW_TZ = pytz.timezone("Europe/Moscow")

    @classmethod
    def convert_to_local_time(cls, utc_time: datetime) -> datetime:
        """
        Преобразует время из UTC в московское время (UTC+3).
        """
        if utc_time.tzinfo is None:
            # Если у времени нет информации о часовом поясе, считаем его UTC
            utc_time = pytz.utc.localize(utc_time)

        # Преобразуем в московское время
        moscow_time = utc_time.astimezone(cls.MOSCOW_TZ)

        return moscow_time
