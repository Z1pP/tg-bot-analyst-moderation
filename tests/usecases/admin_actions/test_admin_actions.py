"""Характеризующие тесты use cases админских действий с сообщениями.

Фиксируют текущее поведение:
- DeleteMessageUseCase;
- ReplyToMessageUseCase;
- SendMessageToChatUseCase;
- BroadcastMessageToTrackedChatsUseCase.
"""

from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)

from constants.enums import AdminActionType
from dto import ChatDTO, UserChatsDTO
from dto.message_action import (
    BroadcastResultDTO,
    MessageActionDTO,
    SendMessageDTO,
)
from exceptions import BotBaseException
from exceptions.moderation import MessageDeleteError, MessageSendError
from models import ChatSession
from services import AdminActionLogService, BotMessageService, ChatService
from usecases.admin_actions.broadcast_message_to_tracked_chats import (
    BroadcastMessageToTrackedChatsUseCase,
)
from usecases.admin_actions.delete_message import DeleteMessageUseCase
from usecases.admin_actions.reply_to_message import ReplyToMessageUseCase
from usecases.admin_actions.send_message_to_chat import SendMessageToChatUseCase
from usecases.chat_tracking.get_user_tracked_chats import (
    GetUserTrackedChatsUseCase,
)

CHAT_TGID = "-1001234567890"
ARCHIVE_CHAT_TGID = "-1009876543210"
ADMIN_TGID = "777"
ADMIN_USERNAME = "admin"
MESSAGE_ID = 42
ADMIN_MESSAGE_ID = 99


# ---------------------------------------------------------------------------
# Общие фикстуры и хелперы
# ---------------------------------------------------------------------------


def make_chat(
    archive_chat_id: Optional[str] = None,
    title: str = "Тестовый чат",
) -> MagicMock:
    """Создаёт мок ChatSession с заданным архивным чатом."""
    chat = MagicMock(spec=ChatSession)
    chat.chat_id = CHAT_TGID
    chat.title = title
    chat.archive_chat_id = archive_chat_id
    return chat


def bad_request(message: str) -> TelegramBadRequest:
    """Создаёт TelegramBadRequest с указанным текстом."""
    return TelegramBadRequest(method=MagicMock(), message=message)


def forbidden(message: str) -> TelegramForbiddenError:
    """Создаёт TelegramForbiddenError с указанным текстом."""
    return TelegramForbiddenError(method=MagicMock(), message=message)


@pytest.fixture
def mock_bot_message_service() -> AsyncMock:
    return AsyncMock(spec=BotMessageService)


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    return AsyncMock(spec=ChatService)


@pytest.fixture
def mock_admin_action_log_service() -> AsyncMock:
    return AsyncMock(spec=AdminActionLogService)


@pytest.fixture
def message_action_dto() -> MessageActionDTO:
    return MessageActionDTO(
        chat_tgid=CHAT_TGID,
        message_id=MESSAGE_ID,
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )


# ---------------------------------------------------------------------------
# DeleteMessageUseCase
# ---------------------------------------------------------------------------


@pytest.fixture
def delete_message_usecase(
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> DeleteMessageUseCase:
    return DeleteMessageUseCase(
        bot_message_service=mock_bot_message_service,
        chat_service=mock_chat_service,
        admin_action_log_service=mock_admin_action_log_service,
    )


@pytest.mark.asyncio
async def test_delete_without_archive_chat_deletes_and_logs(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Без архива сообщение удаляется, пересылки и отчёта нет, действие логируется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.delete_message_from_chat.return_value = True

    # Act
    await delete_message_usecase.execute(message_action_dto)

    # Assert
    mock_chat_service.get_chat_with_archive.assert_awaited_once_with(
        chat_tgid=CHAT_TGID
    )
    mock_bot_message_service.forward_message.assert_not_called()
    mock_bot_message_service.delete_message_from_chat.assert_awaited_once_with(
        chat_id=CHAT_TGID,
        message_id=MESSAGE_ID,
    )
    mock_bot_message_service.send_chat_message.assert_not_called()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.DELETE_MESSAGE,
    )


@pytest.mark.asyncio
async def test_delete_when_chat_not_found_still_deletes(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Если чат не найден, архива нет: удаление выполняется без отчёта."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = None
    mock_bot_message_service.delete_message_from_chat.return_value = True

    # Act
    await delete_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.forward_message.assert_not_called()
    mock_bot_message_service.delete_message_from_chat.assert_awaited_once()
    mock_bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_delete_with_archive_chat_forwards_before_deleting_and_reports(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """С архивом сообщение сначала пересылается, затем удаляется, затем отчёт."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat(title="Рабочий чат")

    call_order: List[str] = []

    async def forward_side_effect(**kwargs) -> None:
        call_order.append("forward")

    async def delete_side_effect(**kwargs) -> bool:
        call_order.append("delete")
        return True

    async def report_side_effect(**kwargs) -> MagicMock:
        call_order.append("report")
        return MagicMock()

    mock_bot_message_service.forward_message.side_effect = forward_side_effect
    mock_bot_message_service.delete_message_from_chat.side_effect = delete_side_effect
    mock_bot_message_service.send_chat_message.side_effect = report_side_effect

    # Act
    await delete_message_usecase.execute(message_action_dto)

    # Assert
    assert call_order == ["forward", "delete", "report"]
    mock_bot_message_service.forward_message.assert_awaited_once_with(
        chat_tgid=ARCHIVE_CHAT_TGID,
        from_chat_tgid=CHAT_TGID,
        message_tgid=MESSAGE_ID,
    )
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    report_text = mock_bot_message_service.send_chat_message.call_args.kwargs["text"]
    assert "Удалено сообщение ботом" in report_text
    assert "Рабочий чат" in report_text
    assert f"@{ADMIN_USERNAME}" in report_text
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.DELETE_MESSAGE,
    )


@pytest.mark.asyncio
async def test_delete_forward_error_does_not_block_deletion(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Ошибка пересылки в архив проглатывается, удаление всё равно выполняется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat()
    mock_bot_message_service.forward_message.side_effect = bad_request(
        "Bad Request: message to forward not found"
    )
    mock_bot_message_service.delete_message_from_chat.return_value = True

    # Act
    await delete_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.forward_message.assert_awaited_once()
    mock_bot_message_service.delete_message_from_chat.assert_awaited_once_with(
        chat_id=CHAT_TGID,
        message_id=MESSAGE_ID,
    )
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.DELETE_MESSAGE,
    )


@pytest.mark.asyncio
async def test_delete_returns_false_raises_message_delete_error(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """delete_message_from_chat вернул False → MessageDeleteError, лог не пишется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.delete_message_from_chat.return_value = False

    # Act / Assert
    with pytest.raises(MessageDeleteError):
        await delete_message_usecase.execute(message_action_dto)

    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_delete_bad_request_raises_message_send_error(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """TelegramBadRequest при удалении → MessageSendError с текстом ошибки."""
    # Arrange
    error = bad_request("Bad Request: message to delete not found")
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.delete_message_from_chat.side_effect = error

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await delete_message_usecase.execute(message_action_dto)

    assert exc_info.value.error == str(error)
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_delete_forbidden_raises_message_send_error(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """TelegramForbiddenError при удалении → MessageSendError."""
    # Arrange
    error = forbidden("Forbidden: bot is not a member of the chat")
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.delete_message_from_chat.side_effect = error

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await delete_message_usecase.execute(message_action_dto)

    assert exc_info.value.error == str(error)
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_delete_report_failure_is_swallowed(
    delete_message_usecase: DeleteMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Ошибка отправки отчёта в архив не роняет use case, лог действия пишется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat()
    mock_bot_message_service.delete_message_from_chat.return_value = True
    mock_bot_message_service.send_chat_message.side_effect = bad_request(
        "Bad Request: chat not found"
    )

    # Act
    await delete_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.DELETE_MESSAGE,
    )


# ---------------------------------------------------------------------------
# ReplyToMessageUseCase
# ---------------------------------------------------------------------------


@pytest.fixture
def reply_to_message_usecase(
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> ReplyToMessageUseCase:
    return ReplyToMessageUseCase(
        bot_message_service=mock_bot_message_service,
        chat_service=mock_chat_service,
        admin_action_log_service=mock_admin_action_log_service,
    )


@pytest.mark.asyncio
async def test_reply_without_admin_message_id_raises_message_send_error(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> None:
    """Без admin_message_id копирование не выполняется и поднимается MessageSendError."""
    # Arrange
    dto = MessageActionDTO(
        chat_tgid=CHAT_TGID,
        message_id=MESSAGE_ID,
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=None,
    )

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await reply_to_message_usecase.execute(dto)

    assert exc_info.value.error == "Отсутствует сообщение для копирования"
    mock_bot_message_service.copy_message_as_reply.assert_not_called()
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_reply_success_without_archive_logs_action(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Успешная копия без архива: логируется REPLY_MESSAGE с названием чата."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_chat_service.get_chat.return_value = make_chat(title="Рабочий чат")
    mock_bot_message_service.copy_message_as_reply.return_value = 555

    # Act
    await reply_to_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.copy_message_as_reply.assert_awaited_once_with(
        chat_tgid=CHAT_TGID,
        from_chat_tgid=ADMIN_TGID,
        message_id=ADMIN_MESSAGE_ID,
        reply_to_message_id=MESSAGE_ID,
    )
    mock_bot_message_service.send_chat_message.assert_not_called()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.REPLY_MESSAGE,
        details="Чат: Рабочий чат",
    )


@pytest.mark.asyncio
async def test_reply_copy_returns_empty_raises_message_send_error(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Пустой результат копирования → MessageSendError, лог не пишется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message_as_reply.return_value = None

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await reply_to_message_usecase.execute(message_action_dto)

    assert "Не удалось скопировать сообщение" in exc_info.value.error
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_reply_message_not_found_uses_special_error_text(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """TelegramBadRequest 'message to copy not found' → текст про ненайденное сообщение."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message_as_reply.side_effect = bad_request(
        "Bad Request: message to copy not found"
    )

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await reply_to_message_usecase.execute(message_action_dto)

    assert "Сообщение для копирования не найдено" in exc_info.value.error
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_reply_other_bad_request_uses_generic_error_text(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Прочий TelegramBadRequest → общий текст ошибки отправки ответа."""
    # Arrange
    error = bad_request("Bad Request: chat not found")
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message_as_reply.side_effect = error

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await reply_to_message_usecase.execute(message_action_dto)

    assert "Ошибка при отправке ответа" in exc_info.value.error
    assert str(error) in exc_info.value.error
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_reply_with_archive_sends_report_with_message_link(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """С архивом отправляется отчёт со ссылкой на скопированное сообщение."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat(title="Рабочий чат")
    mock_bot_message_service.copy_message_as_reply.return_value = 555

    # Act
    await reply_to_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    assert (
        mock_bot_message_service.send_chat_message.call_args.kwargs["chat_tgid"]
        == ARCHIVE_CHAT_TGID
    )
    report_text = mock_bot_message_service.send_chat_message.call_args.kwargs["text"]
    assert "Ответ на сообщение" in report_text
    assert "https://t.me/c/1234567890/555" in report_text
    assert f"@{ADMIN_USERNAME}" in report_text
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.REPLY_MESSAGE,
        details="Чат: Рабочий чат",
    )


@pytest.mark.asyncio
async def test_reply_archive_report_failure_is_swallowed(
    reply_to_message_usecase: ReplyToMessageUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    message_action_dto: MessageActionDTO,
) -> None:
    """Ошибка отправки отчёта в архив не мешает логированию ответа."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat()
    mock_bot_message_service.copy_message_as_reply.return_value = 555
    mock_bot_message_service.send_chat_message.side_effect = forbidden(
        "Forbidden: bot was kicked from the chat"
    )

    # Act
    await reply_to_message_usecase.execute(message_action_dto)

    # Assert
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.REPLY_MESSAGE,
        details="Чат: Тестовый чат",
    )


# ---------------------------------------------------------------------------
# SendMessageToChatUseCase
# ---------------------------------------------------------------------------


@pytest.fixture
def send_message_dto() -> SendMessageDTO:
    return SendMessageDTO(
        chat_tgid=CHAT_TGID,
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )


@pytest.fixture
def send_message_to_chat_usecase(
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> SendMessageToChatUseCase:
    return SendMessageToChatUseCase(
        bot_message_service=mock_bot_message_service,
        chat_service=mock_chat_service,
        admin_action_log_service=mock_admin_action_log_service,
    )


@pytest.mark.asyncio
async def test_send_message_success_logs_action(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """Успешная отправка без архива: копирование и лог SEND_MESSAGE."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message.return_value = 101

    # Act
    await send_message_to_chat_usecase.execute(send_message_dto)

    # Assert
    mock_bot_message_service.copy_message.assert_awaited_once_with(
        chat_tgid=CHAT_TGID,
        from_chat_tgid=ADMIN_TGID,
        message_id=ADMIN_MESSAGE_ID,
    )
    mock_bot_message_service.send_chat_message.assert_not_called()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.SEND_MESSAGE,
    )


@pytest.mark.asyncio
async def test_send_message_copy_returns_empty_raises_message_send_error(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """Пустой результат копирования → MessageSendError, лог не пишется."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message.return_value = None

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await send_message_to_chat_usecase.execute(send_message_dto)

    assert exc_info.value.error == "Не удалось скопировать сообщение"
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_bad_request_raises_message_send_error(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """TelegramBadRequest при копировании → MessageSendError с текстом ошибки."""
    # Arrange
    error = bad_request("Bad Request: chat not found")
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message.side_effect = error

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await send_message_to_chat_usecase.execute(send_message_dto)

    assert exc_info.value.error == str(error)
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_forbidden_raises_message_send_error(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """TelegramForbiddenError при копировании → MessageSendError."""
    # Arrange
    error = forbidden("Forbidden: bot was blocked by the user")
    mock_chat_service.get_chat_with_archive.return_value = make_chat()
    mock_bot_message_service.copy_message.side_effect = error

    # Act / Assert
    with pytest.raises(MessageSendError) as exc_info:
        await send_message_to_chat_usecase.execute(send_message_dto)

    assert exc_info.value.error == str(error)
    mock_admin_action_log_service.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_with_archive_sends_report_with_link(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """С архивом отправляется отчёт со ссылкой на отправленное сообщение."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat(title="Рабочий чат")
    mock_bot_message_service.copy_message.return_value = 101

    # Act
    await send_message_to_chat_usecase.execute(send_message_dto)

    # Assert
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    assert (
        mock_bot_message_service.send_chat_message.call_args.kwargs["chat_tgid"]
        == ARCHIVE_CHAT_TGID
    )
    report_text = mock_bot_message_service.send_chat_message.call_args.kwargs["text"]
    assert "Отправлено сообщение" in report_text
    assert "https://t.me/c/1234567890/101" in report_text
    assert "Рабочий чат" in report_text
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.SEND_MESSAGE,
    )


@pytest.mark.asyncio
async def test_send_message_archive_report_failure_is_swallowed(
    send_message_to_chat_usecase: SendMessageToChatUseCase,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
    send_message_dto: SendMessageDTO,
) -> None:
    """Ошибка отправки отчёта в архив не роняет use case и не мешает логу."""
    # Arrange
    mock_chat_service.get_chat_with_archive.return_value = make_chat(
        archive_chat_id=ARCHIVE_CHAT_TGID
    )
    mock_chat_service.get_chat.return_value = make_chat()
    mock_bot_message_service.copy_message.return_value = 101
    mock_bot_message_service.send_chat_message.side_effect = bad_request(
        "Bad Request: chat not found"
    )

    # Act
    await send_message_to_chat_usecase.execute(send_message_dto)

    # Assert
    mock_bot_message_service.send_chat_message.assert_awaited_once()
    mock_admin_action_log_service.log_action.assert_awaited_once_with(
        admin_tg_id=ADMIN_TGID,
        action_type=AdminActionType.SEND_MESSAGE,
    )


# ---------------------------------------------------------------------------
# BroadcastMessageToTrackedChatsUseCase
# ---------------------------------------------------------------------------


def make_user_chats(*chat_tgids: str) -> UserChatsDTO:
    """Создаёт UserChatsDTO с чатами по переданным tg_id."""
    chats = [
        ChatDTO(
            id=index + 1,
            tg_id=chat_tgid,
            title=f"Чат {index + 1}",
            is_antibot_enabled=False,
            is_auto_moderation_enabled=False,
        )
        for index, chat_tgid in enumerate(chat_tgids)
    ]
    return UserChatsDTO(chats=chats, user_id=1, total_count=len(chats))


@pytest.fixture
def mock_get_user_tracked_chats() -> AsyncMock:
    return AsyncMock(spec=GetUserTrackedChatsUseCase)


@pytest.fixture
def mock_send_message_to_chat() -> AsyncMock:
    return AsyncMock(spec=SendMessageToChatUseCase)


@pytest.fixture
def broadcast_usecase(
    mock_get_user_tracked_chats: AsyncMock,
    mock_send_message_to_chat: AsyncMock,
) -> BroadcastMessageToTrackedChatsUseCase:
    return BroadcastMessageToTrackedChatsUseCase(
        get_user_tracked_chats=mock_get_user_tracked_chats,
        send_message_to_chat=mock_send_message_to_chat,
    )


@pytest.mark.asyncio
async def test_broadcast_sends_message_to_every_tracked_chat(
    broadcast_usecase: BroadcastMessageToTrackedChatsUseCase,
    mock_get_user_tracked_chats: AsyncMock,
    mock_send_message_to_chat: AsyncMock,
) -> None:
    """Рассылка обходит все чаты и возвращает количество успехов."""
    # Arrange
    mock_get_user_tracked_chats.execute.return_value = make_user_chats(
        "-1001", "-1002", "-1003"
    )

    # Act
    result = await broadcast_usecase.execute(
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )

    # Assert
    assert result == BroadcastResultDTO(success_count=3, failed_count=0)
    mock_get_user_tracked_chats.execute.assert_awaited_once_with(tg_id=ADMIN_TGID)
    mock_send_message_to_chat.execute.assert_has_awaits(
        [
            call(
                SendMessageDTO(
                    chat_tgid="-1001",
                    admin_tgid=ADMIN_TGID,
                    admin_username=ADMIN_USERNAME,
                    admin_message_id=ADMIN_MESSAGE_ID,
                )
            ),
            call(
                SendMessageDTO(
                    chat_tgid="-1002",
                    admin_tgid=ADMIN_TGID,
                    admin_username=ADMIN_USERNAME,
                    admin_message_id=ADMIN_MESSAGE_ID,
                )
            ),
            call(
                SendMessageDTO(
                    chat_tgid="-1003",
                    admin_tgid=ADMIN_TGID,
                    admin_username=ADMIN_USERNAME,
                    admin_message_id=ADMIN_MESSAGE_ID,
                )
            ),
        ]
    )


@pytest.mark.asyncio
async def test_broadcast_partial_errors_do_not_stop_other_chats(
    broadcast_usecase: BroadcastMessageToTrackedChatsUseCase,
    mock_get_user_tracked_chats: AsyncMock,
    mock_send_message_to_chat: AsyncMock,
) -> None:
    """Ошибки отдельных чатов считаются, но не прерывают рассылку."""
    # Arrange
    mock_get_user_tracked_chats.execute.return_value = make_user_chats(
        "-1001", "-1002", "-1003", "-1004"
    )
    mock_send_message_to_chat.execute.side_effect = [
        None,
        MessageSendError("copy failed"),
        bad_request("Bad Request: chat not found"),
        BotBaseException(),
    ]

    # Act
    result = await broadcast_usecase.execute(
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )

    # Assert
    assert result == BroadcastResultDTO(success_count=1, failed_count=3)
    assert mock_send_message_to_chat.execute.await_count == 4


@pytest.mark.asyncio
async def test_broadcast_without_tracked_chats_returns_zeros(
    broadcast_usecase: BroadcastMessageToTrackedChatsUseCase,
    mock_get_user_tracked_chats: AsyncMock,
    mock_send_message_to_chat: AsyncMock,
) -> None:
    """Пустой список чатов: отправка не вызывается, результат 0/0."""
    # Arrange
    mock_get_user_tracked_chats.execute.return_value = make_user_chats()

    # Act
    result = await broadcast_usecase.execute(
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )

    # Assert
    assert result == BroadcastResultDTO(success_count=0, failed_count=0)
    mock_send_message_to_chat.execute.assert_not_called()


@pytest.mark.asyncio
async def test_broadcast_logs_action_for_each_successful_send(
    mock_get_user_tracked_chats: AsyncMock,
    mock_bot_message_service: AsyncMock,
    mock_chat_service: AsyncMock,
    mock_admin_action_log_service: AsyncMock,
) -> None:
    """С реальным SendMessageToChatUseCase лог SEND_MESSAGE пишется на каждый успех."""
    # Arrange
    send_message_to_chat = SendMessageToChatUseCase(
        bot_message_service=mock_bot_message_service,
        chat_service=mock_chat_service,
        admin_action_log_service=mock_admin_action_log_service,
    )
    broadcast = BroadcastMessageToTrackedChatsUseCase(
        get_user_tracked_chats=mock_get_user_tracked_chats,
        send_message_to_chat=send_message_to_chat,
    )
    mock_get_user_tracked_chats.execute.return_value = make_user_chats(
        "-1001", "-1002", "-1003"
    )
    # Второй чат возвращает пустой результат — отправка считается неуспешной.
    mock_bot_message_service.copy_message.side_effect = [101, None, 102]
    mock_chat_service.get_chat_with_archive.return_value = None

    # Act
    result = await broadcast.execute(
        admin_tgid=ADMIN_TGID,
        admin_username=ADMIN_USERNAME,
        admin_message_id=ADMIN_MESSAGE_ID,
    )

    # Assert
    assert result == BroadcastResultDTO(success_count=2, failed_count=1)
    assert mock_admin_action_log_service.log_action.await_count == 2
    for awaited_call in mock_admin_action_log_service.log_action.await_args_list:
        assert awaited_call.kwargs["admin_tg_id"] == ADMIN_TGID
        assert awaited_call.kwargs["action_type"] == AdminActionType.SEND_MESSAGE


@pytest.mark.asyncio
async def test_broadcast_unexpected_exception_propagates(
    broadcast_usecase: BroadcastMessageToTrackedChatsUseCase,
    mock_get_user_tracked_chats: AsyncMock,
    mock_send_message_to_chat: AsyncMock,
) -> None:
    """Характеризующий тест: неожиданное исключение не перехватывается и рвёт рассылку."""
    # Arrange
    mock_get_user_tracked_chats.execute.return_value = make_user_chats("-1001", "-1002")
    mock_send_message_to_chat.execute.side_effect = RuntimeError("boom")

    # Act / Assert
    with pytest.raises(RuntimeError, match="boom"):
        await broadcast_usecase.execute(
            admin_tgid=ADMIN_TGID,
            admin_username=ADMIN_USERNAME,
            admin_message_id=ADMIN_MESSAGE_ID,
        )

    assert mock_send_message_to_chat.execute.await_count == 1
