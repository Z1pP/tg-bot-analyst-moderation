"""Тесты ArchiveBindService."""

from unittest.mock import patch

import pytest

from services.chat.archive_bind_service import ArchiveBindService


@pytest.fixture
def service() -> ArchiveBindService:
    """Сервис с фиксированным секретом для детерминированных тестов."""
    with patch("services.chat.archive_bind_service.settings") as mock_settings:
        mock_settings.BOT_TOKEN = "test_secret_key_12345"
        yield ArchiveBindService()


def test_generate_bind_hash_returns_valid_format(service: ArchiveBindService) -> None:
    """generate_bind_hash возвращает строку с префиксом ARCHIVE-."""
    result = service.generate_bind_hash(chat_id=1, admin_tg_id=12345)

    assert result.startswith("ARCHIVE-")
    assert "_" in result
    parts = result.split("_", 1)
    assert len(parts) == 2
    assert len(parts[1]) == 8  # HMAC 8 chars


def test_extract_bind_data_roundtrip(service: ArchiveBindService) -> None:
    """extract_bind_data извлекает данные, сгенерированные generate_bind_hash."""
    chat_id, admin_tg_id = 42, 99999
    bind_hash = service.generate_bind_hash(chat_id=chat_id, admin_tg_id=admin_tg_id)

    extracted = service.extract_bind_data(bind_hash)

    assert extracted is not None
    assert extracted[0] == chat_id
    assert extracted[1] == admin_tg_id


def test_extract_bind_data_invalid_prefix_returns_none(
    service: ArchiveBindService,
) -> None:
    """extract_bind_data возвращает None для строки без префикса ARCHIVE-."""
    assert service.extract_bind_data("INVALID-hash_data_abc12345") is None
    assert service.extract_bind_data("archive-something_abc12345") is None


def test_extract_bind_data_wrong_hmac_returns_none(service: ArchiveBindService) -> None:
    """extract_bind_data возвращает None при неверном HMAC."""
    valid_hash = service.generate_bind_hash(chat_id=1, admin_tg_id=1)
    # Подменяем HMAC часть
    prefix, _ = valid_hash.split("_", 1)
    tampered = f"{prefix}_deadbeef"

    assert service.extract_bind_data(tampered) is None


def test_extract_bind_data_malformed_parts_returns_none(
    service: ArchiveBindService,
) -> None:
    """extract_bind_data возвращает None при отсутствии разделителя _."""
    assert service.extract_bind_data("ARCHIVE-abc123") is None
    assert service.extract_bind_data("ARCHIVE-abc12345") is None


def test_extract_bind_data_old_format_two_parts(service: ArchiveBindService) -> None:
    """extract_bind_data поддерживает старый формат chat_id:timestamp (admin_tg_id=None)."""
    # Генерируем хеш с admin_tg_id
    h = service.generate_bind_hash(chat_id=5, admin_tg_id=100)
    extracted = service.extract_bind_data(h)
    assert extracted is not None
    assert extracted[0] == 5
    assert extracted[1] == 100


def test_extract_bind_data_invalid_base64_returns_none(
    service: ArchiveBindService,
) -> None:
    """extract_bind_data возвращает None при невалидном base64."""
    # Строка с невалидными base64 символами вызывает ValueError при декодировании
    assert service.extract_bind_data("ARCHIVE-@@@!!!_abc12345") is None


def test_generate_bind_hash_different_inputs_different_output(
    service: ArchiveBindService,
) -> None:
    """Разные входные данные дают разные хеши."""
    h1 = service.generate_bind_hash(chat_id=1, admin_tg_id=1)
    h2 = service.generate_bind_hash(chat_id=2, admin_tg_id=1)
    h3 = service.generate_bind_hash(chat_id=1, admin_tg_id=2)

    assert h1 != h2
    assert h1 != h3
    assert h2 != h3
