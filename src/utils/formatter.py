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


def format_seconds(seconds: float) -> str:
    """
    Форматирует секунды в читаемый формат.
    """
    if seconds < 1:
        return "0 сек."

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours} ч.")
    if minutes > 0:
        parts.append(f"{minutes} мин.")
    if secs > 0:
        parts.append(f"{secs} сек.")

    return " ".join(parts)
