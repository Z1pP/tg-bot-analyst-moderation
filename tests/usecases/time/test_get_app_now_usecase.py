"""Тесты для GetAppNowUseCase."""

from datetime import datetime, timezone
from unittest.mock import patch

from dto.time_dto import GetAppNowDTO
from usecases.time.get_app_now import GetAppNowUseCase


def test_get_app_now_returns_service_now() -> None:
    """execute возвращает TimeZoneService.now()."""
    with patch("usecases.time.get_app_now.TimeZoneService") as mock_tz:
        expected = datetime(2025, 2, 1, 12, 0, tzinfo=timezone.utc)
        mock_tz.now.return_value = expected
        use_case = GetAppNowUseCase()
        dto = GetAppNowDTO()
        result = use_case.execute(dto)
        assert result == expected
        mock_tz.now.assert_called_once()
