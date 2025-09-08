import logging
from typing import Tuple

from aiogram import Bot, Router, types

from constants.enums import ReactionAction
from container import container
from dto import MessageReactionDTO
from models import ChatSession, User
from services.chat import ChatService
from services.user import UserService
from usecases.reactions import SaveMessageReactionUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message_reaction()
async def reaction_handler(event: types.MessageReactionUpdated, bot: Bot) -> None:
    try:
        sender, chat = await _get_sender_and_chat(event)

        reaction_dto = MessageReactionDTO(
            chat_id=chat.id,
            user_id=sender.id,
            message_id=str(event.message_id),
            action=_get_reaction_action(event),
            emoji=_get_emoji(event),
            message_url=_generate_message_url(event),
        )

        await save_reacion(reaction_dto=reaction_dto)

    except Exception as e:
        logger.error(f"Ошибка при обработке реакции: {e}", exc_info=True)
        return


async def save_reacion(reaction_dto: MessageReactionDTO) -> None:
    """
    Сохраняет реакцию в базу данных.
    """
    usecase: SaveMessageReactionUseCase = container.resolve(SaveMessageReactionUseCase)
    await usecase.execute(reaction_dto=reaction_dto)


def _get_emoji(event: types.MessageReactionUpdated) -> str:
    """
    Получает эмодзи из сообщения.
    """
    if event.new_reaction:
        return event.new_reaction[0].emoji
    elif event.old_reaction:
        return event.old_reaction[0].emoji
    else:
        return "Неизвестно"


def _get_reaction_action(event: types.MessageReactionUpdated) -> ReactionAction:
    """
    Определяет действие с реакцией.
    """
    old_count = len(event.old_reaction)
    new_count = len(event.new_reaction)

    if new_count > old_count:
        return ReactionAction.ADDED
    elif new_count < old_count:
        return ReactionAction.REMOVED
    else:
        return ReactionAction.CHANGED


def _generate_message_url(event: types.MessageReactionUpdated) -> str:
    """
    Генерирует ссылку на сообщение.
    """
    chat_id = str(event.chat.id)
    message_id = event.message_id

    if chat_id.startswith("-100"):
        # Супергруппы: убираем -100
        clean_chat_id = chat_id[4:]
        return f"https://t.me/c/{clean_chat_id}/{message_id}"
    elif chat_id.startswith("-"):
        # Обычные группы: убираем только -
        clean_chat_id = chat_id[1:]
        return f"https://t.me/c/{clean_chat_id}/{message_id}"
    else:
        # Каналы (положительный ID)
        return f"https://t.me/c/{chat_id}/{message_id}"


async def _get_sender_and_chat(
    event: types.MessageReactionUpdated,
) -> Tuple[User, ChatSession]:
    """
    Получает пользователя и чат из сообщения.
    """
    # Получаем сервисы
    user_service: UserService = container.resolve(UserService)
    chat_service: ChatService = container.resolve(ChatService)

    # Получаем пользователя и чат
    username = event.user.username
    tg_id = str(event.user.id)
    chat_id = str(event.chat.id)

    if not username:
        logger.warning("Пользователь без username: %s", event.user.id)
        return

    sender = await user_service.get_or_create(username=username, tg_id=tg_id)

    chat = await chat_service.get_or_create_chat(
        chat_id=chat_id, title=event.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return

    return sender, chat
