from datetime import datetime


def format_selected_period(start_date: datetime, end_date: datetime) -> str:
    months = (
        "янв.",
        "февр.",
        "мар.",
        "апр.",
        "мая",
        "июн.",
        "июл.",
        "авг.",
        "сент.",
        "окт.",
        "нояб.",
        "дек.",
    )
    start_month = months[start_date.month - 1]

    # Если это один день, показываем только одну дату
    if start_date.date() == end_date.date():
        return f"{start_date.day} {start_month}"

    end_month = months[end_date.month - 1]
    return f"{start_date.day} {start_month} - {end_date.day} {end_month}"


def format_duration(seconds: float | int, include_days: bool = True) -> str:
    """
    Форматирует длительность в читаемый формат.

    Args:
        seconds: Количество секунд.
        include_days: Нужно ли выделять дни (по умолчанию True).
    """
    if seconds < 1:
        return "0 сек."

    seconds = int(seconds)
    parts = []

    if include_days:
        days = seconds // 86400
        if days > 0:
            parts.append(f"{days} д.")
        seconds %= 86400

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        parts.append(f"{hours} ч.")
    if minutes > 0:
        parts.append(f"{minutes} мин.")
    if secs > 0:
        parts.append(f"{secs} сек.")

    return " ".join(parts)


def format_seconds(seconds: float | int) -> str:
    """Псевдоним для format_duration без выделения дней."""
    return format_duration(seconds, include_days=False)
