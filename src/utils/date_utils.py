from datetime import datetime


def validate_and_normalize_period(
    date: datetime | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime]:
    """
    Нормализует период: если передана конкретная дата, устанавливает
    диапазон от начала до конца этого дня. Если даты нет, проверяет наличие периода.

    Args:
        date: Конкретная дата
        start_date: Начало периода
        end_date: Конец периода

    Returns:
        tuple[datetime, datetime]: (start_date, end_date)

    Raises:
        ValueError: Если не указана ни дата, ни период
    """
    if date and not (start_date and end_date):
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)

    if not start_date or not end_date:
        raise ValueError("Необходимо указать дату или период (start_date и end_date)")

    return start_date, end_date
