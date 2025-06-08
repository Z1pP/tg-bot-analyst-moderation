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
    if seconds < 60:
        return f"{round(seconds, 1)} сек."
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{round(minutes, 1)} мин."
    else:
        hours = seconds / 3600
        return f"{round(hours, 1)} ч."
