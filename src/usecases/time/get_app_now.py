"""Use case: получение текущего времени в часовом поясе приложения."""

from datetime import datetime

from dto.time_dto import GetAppNowDTO
from services.time_service import TimeZoneService


class GetAppNowUseCase:
    """Возвращает текущее время в настроенной временной зоне приложения."""

    def execute(self, dto: GetAppNowDTO) -> datetime:
        return TimeZoneService.now()
