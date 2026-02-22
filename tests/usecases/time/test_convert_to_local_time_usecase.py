"""Тесты для ConvertToLocalTimeUseCase."""

from datetime import datetime, timezone
from unittest.mock import patch

from dto.time_dto import ConvertToLocalTimeDTO
from usecases.time.convert_to_local_time import ConvertToLocalTimeUseCase


def test_convert_to_local_time_returns_service_result() -> None:
    """execute делегирует в TimeZoneService и возвращает результат."""
    with patch("usecases.time.convert_to_local_time.TimeZoneService") as mock_tz:
        expected = datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc)
        mock_tz.convert_to_local_time.return_value = expected
        use_case = ConvertToLocalTimeUseCase()
        dto = ConvertToLocalTimeDTO(dt=datetime(2025, 1, 15, 9, 0, tzinfo=timezone.utc))
        result = use_case.execute(dto)
        assert result == expected
        mock_tz.convert_to_local_time.assert_called_once_with(dt=dto.dt)


def test_convert_to_local_time_none_dt() -> None:
    """При dt=None сервис может вернуть None."""
    with patch("usecases.time.convert_to_local_time.TimeZoneService") as mock_tz:
        mock_tz.convert_to_local_time.return_value = None
        use_case = ConvertToLocalTimeUseCase()
        dto = ConvertToLocalTimeDTO(dt=None)
        result = use_case.execute(dto)
        assert result is None
