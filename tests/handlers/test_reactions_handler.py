from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.types import Chat, MessageReactionUpdated, ReactionTypeEmoji
from aiogram.types import User as TGUser
from punq import Container

from constants.enums import ReactionAction
from handlers.group.reactions import reaction_handler
from models import ChatSession
from models import User as DBUser
from services.chat import ChatService
from services.user import UserService
from usecases.reactions import SaveMessageReactionUseCase


@pytest.fixture
def mock_reaction_services(mock_container: Container) -> dict:
    """Фикстура для настройки моков сервисов реакций."""
    user_service = AsyncMock(spec=UserService)
    chat_service = AsyncMock(spec=ChatService)
    save_reaction_usecase = AsyncMock(spec=SaveMessageReactionUseCase)

    def side_effect(cls):
        if cls == UserService:
            return user_service
        if cls == ChatService:
            return chat_service
        if cls == SaveMessageReactionUseCase:
            return save_reaction_usecase
        return MagicMock()

    mock_container.resolve.side_effect = side_effect

    return {
        "user": user_service,
        "chat": chat_service,
        "save_reaction": save_reaction_usecase,
    }


@pytest.mark.asyncio
async def test_reaction_handler_added_supergroup(
    mock_container: Container, mock_reaction_services: dict
) -> None:
    """
    Тестирует добавление реакции в супергруппе.

    Проверяет:
    1. Определение действия ReactionAction.ADDED.
    2. Генерацию ссылки на сообщение для супергруппы (-100...).
    3. Вызов SaveMessageReactionUseCase.
    """
    # 1. Данные для моков
    db_user = MagicMock(spec=DBUser)
    db_user.id = 1
    mock_reaction_services["user"].get_or_create.return_value = db_user

    db_chat = MagicMock(spec=ChatSession)
    db_chat.id = 10
    mock_reaction_services["chat"].get_or_create.return_value = db_chat

    # 2. Мок события
    bot = AsyncMock(spec=Bot)
    event = MagicMock(spec=MessageReactionUpdated)
    event.message_id = 123

    event.user = MagicMock(spec=TGUser)
    event.user.id = 111
    event.user.username = "test_user"
    event.user.is_bot = False

    event.chat = MagicMock(spec=Chat)
    event.chat.id = -100123456
    event.chat.title = "Supergroup"

    emoji = ReactionTypeEmoji(emoji="👍")
    event.new_reaction = [emoji]
    event.old_reaction = []

    # 3. Вызов
    await reaction_handler(event=event, bot=bot, container=mock_container)

    # 4. Проверки
    mock_reaction_services["save_reaction"].execute.assert_called_once()
    dto = mock_reaction_services["save_reaction"].execute.call_args.kwargs[
        "reaction_dto"
    ]
    assert dto.action == ReactionAction.ADDED
    assert dto.emoji == "👍"
    assert dto.message_url == "https://t.me/c/123456/123"


@pytest.mark.asyncio
async def test_reaction_handler_removed_regular_group(
    mock_container: Container, mock_reaction_services: dict
) -> None:
    """
    Тестирует удаление реакции в обычной группе.

    Проверяет:
    1. Определение действия ReactionAction.REMOVED.
    2. Генерацию ссылки на сообщение для обычной группы (-...).
    """
    # 1. Данные для моков
    db_user = MagicMock(spec=DBUser)
    db_user.id = 1
    mock_reaction_services["user"].get_or_create.return_value = db_user

    db_chat = MagicMock(spec=ChatSession)
    db_chat.id = 10
    mock_reaction_services["chat"].get_or_create.return_value = db_chat

    # 2. Мок события (удаление реакции)
    bot = AsyncMock(spec=Bot)
    event = MagicMock(spec=MessageReactionUpdated)
    event.message_id = 456

    event.user = MagicMock(spec=TGUser)
    event.user.id = 111
    event.user.username = "test_user"
    event.user.is_bot = False

    event.chat = MagicMock(spec=Chat)
    event.chat.id = -789
    event.chat.title = "Regular Group"

    emoji = ReactionTypeEmoji(emoji="🔥")
    event.new_reaction = []
    event.old_reaction = [emoji]

    # 3. Вызов
    await reaction_handler(event=event, bot=bot, container=mock_container)

    # 4. Проверки
    dto = mock_reaction_services["save_reaction"].execute.call_args.kwargs[
        "reaction_dto"
    ]
    assert dto.action == ReactionAction.REMOVED
    assert dto.emoji == "🔥"
    assert dto.message_url == "https://t.me/c/789/456"


@pytest.mark.asyncio
async def test_reaction_handler_no_chat_error(
    mock_container: Container, mock_reaction_services: dict
) -> None:
    """
    Тестирует обработку события с минимальными данными.

    Хендлер строит DTO из event и вызывает SaveMessageReactionUseCase
    (проверка «чат не найден» в текущей реализации не выполняется).
    """
    # 1. Мок события с минимальным набором полей
    bot = AsyncMock(spec=Bot)
    event = MagicMock(spec=MessageReactionUpdated)
    event.message_id = 1
    event.user = MagicMock(spec=TGUser)
    event.user.id = 111
    event.user.is_bot = False
    event.chat = MagicMock(spec=Chat)
    event.chat.id = -100123
    event.new_reaction = []
    event.old_reaction = []

    # 2. Вызов
    await reaction_handler(event=event, bot=bot, container=mock_container)

    # 3. Хендлер всегда вызывает save_reaction с DTO из event
    mock_reaction_services["save_reaction"].execute.assert_called_once()
