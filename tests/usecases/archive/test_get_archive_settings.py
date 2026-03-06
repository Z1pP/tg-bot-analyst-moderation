"""Тесты GetArchiveSettingsUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from constants import Dialog
from dto import GetChatWithArchiveDTO
from exceptions.base import BotBaseException
from usecases.archive.get_archive_settings import (
    ArchiveSettingsResult,
    GetArchiveSettingsUseCase,
)


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot_permission_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_report_schedule_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot_message_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def usecase(
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> GetArchiveSettingsUseCase:
    return GetArchiveSettingsUseCase(
        chat_service=mock_chat_service,
        bot_permission_service=mock_bot_permission_service,
        report_schedule_service=mock_report_schedule_service,
        bot_message_service=mock_bot_message_service,
    )


@pytest.mark.asyncio
async def test_execute_chat_not_found_returns_not_found_message(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
) -> None:
    """При отсутствии чата возвращается сообщение о ненайденном чате."""
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=None)

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    assert isinstance(result, ArchiveSettingsResult)
    assert result.text == Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
    assert result.reply_markup is not None


@pytest.mark.asyncio
async def test_execute_chat_without_archive_returns_missing_message(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
) -> None:
    """При чате без архива возвращается сообщение об отсутствии архива."""
    chat = MagicMock()
    chat.archive_chat = None
    chat.archive_chat_id = None
    chat.title = "Test Chat"
    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    assert isinstance(result, ArchiveSettingsResult)
    assert "Test Chat" in result.text
    assert result.reply_markup is not None


@pytest.mark.asyncio
async def test_execute_chat_with_archive_and_insufficient_permissions(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
) -> None:
    """При недостаточных правах в архиве возвращается сообщение об ошибке."""
    archive_chat = MagicMock()
    archive_chat.chat_id = "-200"
    archive_chat.title = "Archive"
    chat = MagicMock()
    chat.archive_chat = archive_chat
    chat.archive_chat_id = "-200"
    chat.title = "Work Chat"

    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_bot_permission_service.get_chat_from_telegram = AsyncMock(
        return_value=MagicMock(title="Archive")
    )
    mock_bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=MagicMock(
            has_all_permissions=False,
            missing_permissions=["Блокировка и мут пользователей"],
        )
    )

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    assert isinstance(result, ArchiveSettingsResult)
    assert "Archive" in result.text
    assert "Блокировка и мут пользователей" in result.text


@pytest.mark.asyncio
async def test_execute_chat_with_archive_and_all_permissions(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> None:
    """При полных правах возвращается успешный результат с расписанием."""
    archive_chat = MagicMock()
    archive_chat.chat_id = "-200"
    archive_chat.title = "Archive"
    chat = MagicMock()
    chat.archive_chat = archive_chat
    chat.archive_chat_id = "-200"
    chat.title = "Work Chat"
    chat.id = 1

    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_chat_service.update_chat_title = AsyncMock(return_value=archive_chat)
    mock_bot_permission_service.get_chat_from_telegram = AsyncMock(
        return_value=MagicMock(title="Archive")
    )
    mock_bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=MagicMock(has_all_permissions=True)
    )
    mock_report_schedule_service.get_schedule = AsyncMock(return_value=None)
    mock_bot_message_service.get_chat_invite_link = AsyncMock(
        return_value="https://t.me/joinchat/xxx"
    )

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    assert isinstance(result, ArchiveSettingsResult)
    assert "Work Chat" in result.text
    assert result.reply_markup is not None


@pytest.mark.asyncio
async def test_execute_raises_bot_base_exception_on_generic_error(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
) -> None:
    """При неожиданной ошибке пробрасывается BotBaseException."""
    mock_chat_service.get_chat_with_archive = AsyncMock(
        side_effect=RuntimeError("DB error")
    )

    dto = GetChatWithArchiveDTO(chat_id=1)

    with pytest.raises(BotBaseException) as exc_info:
        await usecase.execute(dto)

    assert exc_info.value.get_user_message() is not None


@pytest.mark.asyncio
async def test_execute_re_raises_bot_base_exception(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
) -> None:
    """BotBaseException из get_chat_with_archive пробрасывается без обёртки."""
    mock_chat_service.get_chat_with_archive = AsyncMock(
        side_effect=BotBaseException(message="Chat error")
    )

    dto = GetChatWithArchiveDTO(chat_id=1)

    with pytest.raises(BotBaseException) as exc_info:
        await usecase.execute(dto)

    assert exc_info.value.message == "Chat error"


@pytest.mark.asyncio
async def test_execute_syncs_archive_title_when_renamed_in_telegram(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> None:
    """Синхронизация title архивного чата при переименовании в Telegram."""
    archive_chat = MagicMock()
    archive_chat.id = 2
    archive_chat.chat_id = "-200"
    archive_chat.title = "Old Archive Title"
    chat = MagicMock()
    chat.archive_chat = archive_chat
    chat.archive_chat_id = "-200"
    chat.title = "Work Chat"
    chat.id = 1

    tg_chat = MagicMock()
    tg_chat.title = "New Archive Title"
    updated_archive = MagicMock()
    updated_archive.id = 2
    updated_archive.chat_id = "-200"
    updated_archive.title = "New Archive Title"

    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_chat_service.update_chat_title = AsyncMock(return_value=updated_archive)
    mock_bot_permission_service.get_chat_from_telegram = AsyncMock(
        return_value=tg_chat
    )
    mock_bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=MagicMock(has_all_permissions=True)
    )
    mock_report_schedule_service.get_schedule = AsyncMock(return_value=None)
    mock_bot_message_service.get_chat_invite_link = AsyncMock(
        return_value="https://t.me/joinchat/xxx"
    )

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    mock_chat_service.update_chat_title.assert_called_once_with(
        chat.archive_chat.id, "New Archive Title"
    )
    assert result.reply_markup is not None


@pytest.mark.asyncio
async def test_execute_title_sync_when_update_returns_none_keeps_old(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> None:
    """При update_chat_title=None chat.archive_chat не обновляется."""
    archive_chat = MagicMock()
    archive_chat.id = 2
    archive_chat.chat_id = "-200"
    archive_chat.title = "Old"
    chat = MagicMock()
    chat.archive_chat = archive_chat
    chat.archive_chat_id = "-200"
    chat.title = "Work"
    chat.id = 1

    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_chat_service.update_chat_title = AsyncMock(return_value=None)
    mock_bot_permission_service.get_chat_from_telegram = AsyncMock(
        return_value=MagicMock(title="New")
    )
    mock_bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=MagicMock(has_all_permissions=True)
    )
    mock_report_schedule_service.get_schedule = AsyncMock(return_value=None)
    mock_bot_message_service.get_chat_invite_link = AsyncMock(
        return_value="https://t.me/xxx"
    )

    dto = GetChatWithArchiveDTO(chat_id=1)
    result = await usecase.execute(dto)

    assert chat.archive_chat.title == "Old"
    assert result.reply_markup is not None


@pytest.mark.asyncio
async def test_execute_skips_title_sync_when_titles_match(
    usecase: GetArchiveSettingsUseCase,
    mock_chat_service: AsyncMock,
    mock_bot_permission_service: AsyncMock,
    mock_report_schedule_service: AsyncMock,
    mock_bot_message_service: AsyncMock,
) -> None:
    """Не вызывается update_chat_title когда title совпадает с Telegram."""
    archive_chat = MagicMock()
    archive_chat.id = 2
    archive_chat.chat_id = "-200"
    archive_chat.title = "Archive"
    chat = MagicMock()
    chat.archive_chat = archive_chat
    chat.archive_chat_id = "-200"
    chat.title = "Work Chat"
    chat.id = 1

    mock_chat_service.get_chat_with_archive = AsyncMock(return_value=chat)
    mock_bot_permission_service.get_chat_from_telegram = AsyncMock(
        return_value=MagicMock(title="Archive")
    )
    mock_bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=MagicMock(has_all_permissions=True)
    )
    mock_report_schedule_service.get_schedule = AsyncMock(return_value=None)
    mock_bot_message_service.get_chat_invite_link = AsyncMock(
        return_value="https://t.me/joinchat/xxx"
    )

    dto = GetChatWithArchiveDTO(chat_id=1)
    await usecase.execute(dto)

    mock_chat_service.update_chat_title.assert_not_called()
