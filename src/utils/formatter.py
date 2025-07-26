def format_selected_period(selected_period: str) -> str:
    """
    Форматирует выбранный период в читаемый формат.
    """
    if not selected_period:
        return "указанный период"
    period = selected_period.split("За")[-1]
    return period.strip()


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
        parts.append(f"{hours}ч.")
    if minutes > 0:
        parts.append(f"{minutes}мин.")
    if secs > 0:
        parts.append(f"{secs}сек.")

    return " ".join(parts)
