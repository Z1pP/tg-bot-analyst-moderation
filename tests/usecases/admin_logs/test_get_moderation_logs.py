"""Тесты use case получения логов модерации для API."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from dto.admin_log import AdminLogsPageResultDTO, GetAdminLogsPageDTO
from usecases.admin_logs import GetModerationLogsUseCase


@pytest.mark.asyncio
async def test_get_moderation_logs_maps_repository_rows() -> None:
    """Записи репозитория преобразуются в DTO с данными администратора."""
    admin = MagicMock()
    admin.username = "admin"
    admin.tg_id = "42"
    log = MagicMock()
    log.id = 1
    log.action_type = "ban"
    log.details = "Забанен пользователь"
    log.admin = admin
    log.created_at = datetime(2026, 10, 28, 12, 0)

    repository = MagicMock()
    repository.get_logs_paginated = AsyncMock(return_value=([log], 1))
    usecase = GetModerationLogsUseCase(log_repository=repository)

    result = await usecase.execute(GetAdminLogsPageDTO(page=1, limit=20))

    assert isinstance(result, AdminLogsPageResultDTO)
    assert result.total == 1
    assert result.items[0].admin_username == "admin"
    assert result.items[0].admin_tg_id == "42"
    assert result.items[0].created_at == datetime(2026, 10, 28, 12, 0)
    repository.get_logs_paginated.assert_awaited_once_with(page=1, limit=20)


@pytest.mark.asyncio
async def test_get_moderation_logs_handles_missing_admin() -> None:
    """Если администратор не загружен, поля остаются None."""
    log = MagicMock()
    log.id = 2
    log.action_type = "warn"
    log.details = None
    log.admin = None
    log.created_at = datetime(2026, 10, 28, 12, 0)

    repository = MagicMock()
    repository.get_logs_paginated = AsyncMock(return_value=([log], 1))
    usecase = GetModerationLogsUseCase(log_repository=repository)

    result = await usecase.execute(GetAdminLogsPageDTO())

    assert result.items[0].admin_username is None
    assert result.items[0].admin_tg_id is None