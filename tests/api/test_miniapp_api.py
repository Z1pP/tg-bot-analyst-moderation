"""Тесты Mini App API: роутеры ходят в use cases, а не в репозитории."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.dependencies.container import get_container
from api.dependencies.miniapp import verify_telegram_init_data
from api.main import app
from constants.enums import UserRole
from dto.admin_log import AdminLogItemDTO, AdminLogsPageResultDTO
from dto.stats import ModeratorsStatsDTO, StatsSummaryDTO
from usecases.admin_logs import GetModerationLogsUseCase
from usecases.stats import GetModeratorsStatsUseCase, GetStatsSummaryUseCase
from usecases.user import GetUserByTgIdUseCase


@pytest.fixture
def client() -> TestClient:
    """Клиент с подменой Telegram-аутентификации."""
    app.dependency_overrides[verify_telegram_init_data] = lambda: {
        "user": '{"id": 42, "username": "admin"}'
    }
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _use_container(client: TestClient, container: MagicMock) -> None:
    app.dependency_overrides[get_container] = lambda: container


def test_stats_returns_summary(client: TestClient) -> None:
    """GET /stats возвращает сводку из use case."""
    usecase = MagicMock()
    usecase.execute = AsyncMock(
        return_value=StatsSummaryDTO(
            active_users=3,
            moderation_actions=10,
            today_actions=2,
        )
    )
    container = MagicMock()
    container.resolve.side_effect = lambda cls: {GetStatsSummaryUseCase: usecase}[cls]
    _use_container(client, container)

    response = client.get("/api/v1/miniapp/stats")

    assert response.status_code == 200
    assert response.json() == {
        "active_users": 3,
        "moderation_actions": 10,
        "today_actions": 2,
    }


def test_moderators_stats_rejects_invalid_period(client: TestClient) -> None:
    """Неизвестный период возвращает 400 до обращения к use case."""
    container = MagicMock()
    _use_container(client, container)

    response = client.get("/api/v1/miniapp/stats/moderators?period=nope")

    assert response.status_code == 400
    container.resolve.assert_not_called()


def test_moderators_stats_returns_list(client: TestClient) -> None:
    """GET /stats/moderators сериализует DTO use case."""
    usecase = MagicMock()
    usecase.execute = AsyncMock(
        return_value=ModeratorsStatsDTO(moderators=[], period="За сегодня")
    )
    container = MagicMock()
    container.resolve.side_effect = lambda cls: {
        GetModeratorsStatsUseCase: usecase
    }[cls]
    _use_container(client, container)

    response = client.get("/api/v1/miniapp/stats/moderators?period=За сегодня")

    assert response.status_code == 200
    assert response.json() == {"moderators": [], "period": "За сегодня"}


def test_users_me_returns_user_dto(client: TestClient) -> None:
    """GET /users/me берёт пользователя через GetUserByTgIdUseCase."""
    user = MagicMock()
    user.id = 1
    user.tg_id = "42"
    user.username = "admin"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.language = "ru"
    usecase = MagicMock()
    usecase.execute = AsyncMock(return_value=user)
    container = MagicMock()
    container.resolve.side_effect = lambda cls: {GetUserByTgIdUseCase: usecase}[cls]
    _use_container(client, container)

    response = client.get("/api/v1/miniapp/users/me")

    assert response.status_code == 200
    assert response.json()["tg_id"] == "42"
    usecase.execute.assert_awaited_once_with(tg_id="42")


def test_moderation_log_serializes_dto(client: TestClient) -> None:
    """GET /moderation/log возвращает DTO с ISO-датой."""
    user = MagicMock()
    user.id = 1
    user.tg_id = "42"
    usecase = MagicMock()
    usecase.execute = AsyncMock(
        return_value=AdminLogsPageResultDTO(
            items=[
                AdminLogItemDTO(
                    id=1,
                    action_type="ban",
                    details="тест",
                    admin_username="admin",
                    admin_tg_id="42",
                    created_at=datetime(2026, 10, 28, 12, 0),
                )
            ],
            total=1,
            page=1,
            limit=20,
        )
    )
    get_user = MagicMock()
    get_user.execute = AsyncMock(return_value=user)
    container = MagicMock()
    container.resolve.side_effect = lambda cls: {
        GetModerationLogsUseCase: usecase,
        GetUserByTgIdUseCase: get_user,
    }[cls]
    _use_container(client, container)

    response = client.get("/api/v1/miniapp/moderation/log")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["created_at"] == "2026-10-28T12:00:00"
    assert payload["items"][0]["admin_username"] == "admin"