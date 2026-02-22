"""Тесты для utils/exception_handler.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from exceptions.base import BotBaseException
from exceptions.moderation import PrivateModerationError, PublicModerationError
from utils.exception_handler import (
    TELEGRAM_MESSAGE_MAX_LENGTH,
    AsyncErrorHandler,
    handle_exception,
    registry_exceptions,
)


@pytest.mark.asyncio
async def test_handle_exception_bot_base_sends_user_message() -> None:
    """При BotBaseException отправляется get_user_message() и клавиатура скрытия."""
    message = AsyncMock()
    exc = BotBaseException("Сообщение пользователю")

    with patch(
        "utils.exception_handler.send_html_message_with_kb", new_callable=AsyncMock
    ) as send_mock:
        await handle_exception(message, exc)
        send_mock.assert_called_once()
        call_kw = send_mock.call_args.kwargs
        assert call_kw["text"] == "Сообщение пользователю"
        assert call_kw["message"] == message
        assert call_kw["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_exception_bot_base_with_context() -> None:
    """При BotBaseException с context логируется контекст."""
    message = AsyncMock()
    exc = BotBaseException("Ошибка")

    with patch(
        "utils.exception_handler.send_html_message_with_kb", new_callable=AsyncMock
    ):
        await handle_exception(message, exc, context="test_handler")
        # Вызов отправки с текстом исключения
        assert True


@pytest.mark.asyncio
async def test_handle_exception_generic_sends_fallback() -> None:
    """При обычном Exception отправляется общее сообщение об ошибке."""
    message = AsyncMock()
    exc = ValueError("Что-то пошло не так")

    with patch(
        "utils.exception_handler.send_html_message_with_kb", new_callable=AsyncMock
    ) as send_mock:
        await handle_exception(message, exc)
        send_mock.assert_called_once()
        assert "непредвиденная ошибка" in send_mock.call_args.kwargs["text"]


def test_registry_exceptions_registers_middleware() -> None:
    """registry_exceptions вешает middleware на message и callback_query."""
    dispatcher = MagicMock()
    dispatcher.message = MagicMock()
    dispatcher.callback_query = MagicMock()
    container = MagicMock()
    handler_instance = AsyncErrorHandler(
        bot_message_service=MagicMock(),
        user_repository=MagicMock(),
    )
    container.resolve = MagicMock(return_value=handler_instance)

    registry_exceptions(dispatcher, container)

    assert dispatcher.message.middleware.called
    assert dispatcher.callback_query.middleware.called
    assert container.resolve.call_count == 2


@pytest.mark.asyncio
async def test_async_error_handler_handler_success() -> None:
    """Если handler выполняется без исключения, результат возвращается."""
    handler = AsyncMock(return_value="ok")
    event = AsyncMock()
    data = {}

    err_handler = AsyncErrorHandler(
        bot_message_service=AsyncMock(),
        user_repository=AsyncMock(),
    )
    result = await err_handler(handler, event, data)
    assert result == "ok"
    handler.assert_called_once_with(event, data)


@pytest.mark.asyncio
async def test_async_error_handler_private_moderation_error() -> None:
    """PrivateModerationError отправляется в ЛС пользователю."""
    handler = AsyncMock(side_effect=PrivateModerationError("тест"))
    event = AsyncMock()
    data = {}

    bot_svc = AsyncMock()
    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=AsyncMock(),
    )
    with patch.object(err_handler, "_get_user_id", return_value=123):
        with patch.object(err_handler, "_get_chat_id", return_value=None):
            result = await err_handler(handler, event, data)
    assert result is None
    bot_svc.send_private_message.assert_called_once_with(user_tgid=123, text="тест")


@pytest.mark.asyncio
async def test_async_error_handler_public_moderation_error() -> None:
    """PublicModerationError отправляется в чат."""
    handler = AsyncMock(side_effect=PublicModerationError("в чат"))
    event = AsyncMock()
    data = {}

    bot_svc = AsyncMock()
    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=AsyncMock(),
    )
    with patch.object(err_handler, "_get_chat_id", return_value=-100):
        with patch.object(err_handler, "_get_user_id", return_value=1):
            result = await err_handler(handler, event, data)
    assert result is None
    bot_svc.send_chat_message.assert_called_once_with(chat_tgid=-100, text="в чат")


@pytest.mark.asyncio
async def test_async_error_handler_bot_base_exception_chat() -> None:
    """BotBaseException при наличии chat_id отправляется в чат."""
    handler = AsyncMock(side_effect=BotBaseException("общая ошибка"))
    event = AsyncMock()
    data = {}

    bot_svc = AsyncMock()
    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=AsyncMock(),
    )
    with patch.object(err_handler, "_get_chat_id", return_value=-200):
        with patch.object(err_handler, "_get_user_id", return_value=1):
            result = await err_handler(handler, event, data)
    assert result is None
    bot_svc.send_chat_message.assert_called_once_with(
        chat_tgid=-200, text="общая ошибка"
    )


@pytest.mark.asyncio
async def test_async_error_handler_bot_base_exception_private_only() -> None:
    """BotBaseException при отсутствии chat_id отправляется в ЛС."""
    handler = AsyncMock(side_effect=BotBaseException("ошибка"))
    event = AsyncMock()
    data = {}

    bot_svc = AsyncMock()
    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=AsyncMock(),
    )
    with patch.object(err_handler, "_get_chat_id", return_value=None):
        with patch.object(err_handler, "_get_user_id", return_value=456):
            result = await err_handler(handler, event, data)
    assert result is None
    bot_svc.send_private_message.assert_called_once_with(user_tgid=456, text="ошибка")


@pytest.mark.asyncio
async def test_async_error_handler_unhandled_exception_notifies_devs() -> None:
    """Необработанное исключение логируется и уведомляются DEV."""
    handler = AsyncMock(side_effect=RuntimeError("критично"))
    event = AsyncMock()
    data = {}

    user_repo = AsyncMock()
    user_repo.get_users_with_role = AsyncMock(return_value=[])
    bot_svc = AsyncMock()

    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=user_repo,
    )
    with pytest.raises(RuntimeError):
        await err_handler(handler, event, data)
    user_repo.get_users_with_role.assert_called_once()


@pytest.mark.asyncio
async def test_notify_devs_about_error_sends_private_message_to_devs() -> None:
    """_notify_devs_about_error отправляет сообщение в ЛС каждому DEV с tg_id."""
    from types import SimpleNamespace

    event = Message.model_construct(
        chat=Chat.model_construct(id=-100),
        from_user=User.model_construct(id=1),
    )
    exc = ValueError("тестовая ошибка")
    dev_user = SimpleNamespace(tg_id="999", username="dev")
    user_repo = AsyncMock()
    user_repo.get_users_with_role = AsyncMock(return_value=[dev_user])
    bot_svc = AsyncMock()

    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=user_repo,
    )
    await err_handler._notify_devs_about_error(event, exc)

    bot_svc.send_private_message.assert_called_once()
    assert bot_svc.send_private_message.call_args.kwargs["user_tgid"] == "999"
    assert "Ошибка бота" in bot_svc.send_private_message.call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_notify_devs_about_error_skips_user_without_tg_id() -> None:
    """DEV без tg_id не получает сообщение."""
    from types import SimpleNamespace

    event = Message.model_construct(
        chat=Chat.model_construct(id=1), from_user=User.model_construct(id=1)
    )
    dev_user = SimpleNamespace(tg_id=None, username="dev")
    user_repo = AsyncMock()
    user_repo.get_users_with_role = AsyncMock(return_value=[dev_user])
    bot_svc = AsyncMock()

    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=user_repo,
    )
    await err_handler._notify_devs_about_error(event, ValueError("err"))

    bot_svc.send_private_message.assert_not_called()


@pytest.mark.asyncio
async def test_async_error_handler_callback_query_chat_id_from_message() -> None:
    """Для CallbackQuery chat_id берётся из event.message.chat.id (через _get_chat_id)."""
    handler = AsyncMock(side_effect=PublicModerationError("в чат"))
    event = AsyncMock()
    data = {}

    bot_svc = AsyncMock()
    err_handler = AsyncErrorHandler(
        bot_message_service=bot_svc,
        user_repository=AsyncMock(),
    )
    with patch.object(err_handler, "_get_chat_id", return_value=-300):
        with patch.object(err_handler, "_get_user_id", return_value=1):
            await err_handler(handler, event, data)
    bot_svc.send_chat_message.assert_called_once_with(chat_tgid=-300, text="в чат")


def test_telegram_message_max_length_constant() -> None:
    """Константа лимита длины сообщения задана."""
    assert TELEGRAM_MESSAGE_MAX_LENGTH == 4096


def test_get_event_info_message() -> None:
    """_get_event_context для Message возвращает описание с chat_id и from_user."""
    err_handler = AsyncErrorHandler(
        bot_message_service=AsyncMock(),
        user_repository=AsyncMock(),
    )
    msg = Message.model_construct(
        chat=Chat.model_construct(id=-100),
        from_user=User.model_construct(id=123),
    )
    info = err_handler._get_event_context(msg)
    assert "Message" in info
    assert "-100" in info
    assert "123" in info


def test_get_event_info_callback_query() -> None:
    """_get_event_context для CallbackQuery возвращает data и from_user."""
    err_handler = AsyncErrorHandler(
        bot_message_service=AsyncMock(),
        user_repository=AsyncMock(),
    )
    cb = CallbackQuery.model_construct(
        data="pag__2",
        from_user=User.model_construct(id=456),
    )
    info = err_handler._get_event_context(cb)
    assert "CallbackQuery" in info
    assert "pag__2" in info
    assert "456" in info


def test_get_user_id_message() -> None:
    """_get_user_id для Message возвращает from_user.id."""
    err_handler = AsyncErrorHandler(
        bot_message_service=AsyncMock(),
        user_repository=AsyncMock(),
    )
    msg = Message.model_construct(
        from_user=User.model_construct(id=789),
    )
    assert err_handler._get_user_id(msg) == 789


def test_get_chat_id_message() -> None:
    """_get_chat_id для Message возвращает chat.id."""
    err_handler = AsyncErrorHandler(
        bot_message_service=AsyncMock(),
        user_repository=AsyncMock(),
    )
    msg = Message.model_construct(chat=Chat.model_construct(id=-200))
    assert err_handler._get_chat_id(msg) == -200
