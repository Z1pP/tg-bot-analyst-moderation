"""Use case: конвертация datetime в локальную временную зону приложения."""

from datetime import datetime
from typing import Optional

from dto.time_dto import ConvertToLocalTimeDTO
from services.time_service import TimeZoneService


class ConvertToLocalTimeUseCase:
    """Конвертирует переданную дату/время в локальную зону приложения."""

    def execute(self, dto: ConvertToLocalTimeDTO) -> Optional[datetime]:
        return TimeZoneService.convert_to_local_time(dt=dto.dt)
