import logging

from aiogram import Router
from aiogram.types import Message

from constants.enums import UserRole
from container import container
from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO
from models import ChatSession, User
from models.message import MessageType
from services.chat import ChatService
from services.time_service import TimeZoneService
from services.user import UserService
from usecases.message import (
    SaveMessageUseCase,
    SaveModeratorReplyMessageUseCase,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _get_message_type(message: Message) -> MessageType:
    if message.reply_to_message:
        return MessageType.REPLY
    else:
        return MessageType.MESSAGE


@router.message()
async def group_message_handler(message: Message):
    """
    Обрабатывет сообщения которые приходят от всех пользователей
    """
    # Сообщения от ботов не сохраняются
    if message.from_user.is_bot:
        return

    sender, chat = await _get_sender_and_chat(message=message)

    # Получаем тип сообщения из message
    msg_type = _get_message_type(message=message)

    if sender.role == UserRole.USER:
        await process_user_message(
            message=message,
            sender=sender,
            chat=chat,
        )
        return

    if msg_type == MessageType.REPLY:
        await process_reply_message(
            message=message,
            sender=sender,
            chat=chat,
        )
    else:
        await process_reqular_message(
            message=message,
            sender=sender,
            chat=chat,
        )


async def process_user_message(
    message: Message,
    sender: User,
    chat: ChatSession,
) -> None:
    """
    Обрабатывает обычное сообщение от пользователей
    """
    message_date = TimeZoneService.convert_to_local_time(
        dt=message.date,
    )

    msg_dto = CreateMessageDTO(
        chat_id=chat.id,
        user_id=sender.id,
        message_id=str(message.message_id),
        message_type=MessageType.MESSAGE.value,
        content_type=message.content_type.value,
        text=message.text,
        created_at=message_date,
    )

    try:
        message_usecase: SaveMessageUseCase = container.resolve(SaveMessageUseCase)
        saved_message = await message_usecase.execute(message_dto=msg_dto)

        logger.info(f"Сообщение сохранено: {saved_message}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользотваельного сообщения: {e}")


async def process_reply_message(
    message: Message,
    sender: User,
    chat: ChatSession,
) -> None:
    """
    Обрабатывает reply-сообщения от модераторов и админов
    """
    # Преобразуем время сообщения в локальное время
    message_date = TimeZoneService.convert_to_local_time(
        dt=message.date,
    )
    reply_to_message_date = TimeZoneService.convert_to_local_time(
        dt=message.reply_to_message.date,
    )

    # Создаем DTO для сохранения сообщения
    msg_dto = CreateMessageDTO(
        chat_id=chat.id,
        user_id=sender.id,
        message_id=str(message.message_id),
        message_type=MessageType.REPLY.value,
        content_type=message.content_type.value,
        text=message.text,
        created_at=message_date,
    )

    try:
        # Сохраняем reply как обычное сообщение
        message_usecase: SaveMessageUseCase = container.resolve(SaveMessageUseCase)
        saved_message = await message_usecase.execute(message_dto=msg_dto)

        # Создаем ссылку на оригинальное сообщение
        original_message_url = f"https://t.me/c/{chat.chat_id.lstrip('-')}/{message.reply_to_message.message_id}"

        # DTO для связи reply с оригинальным сообщением
        reply_dto = CreateMessageReplyDTO(
            chat_id=chat.id,
            original_message_url=original_message_url,
            reply_message_id=saved_message.id,
            reply_user_id=sender.id,
            original_message_date=message_date,
            reply_message_date=reply_to_message_date,
            response_time_seconds=(
                message_date - reply_to_message_date
            ).total_seconds(),
        )

        # Сохраняем связь в MessageReply
        reply_usecase: SaveModeratorReplyMessageUseCase = container.resolve(
            SaveModeratorReplyMessageUseCase
        )
        await reply_usecase.execute(reply_message_dto=reply_dto)
    except Exception as e:
        logger.error("Error saving reply message: %s", str(e))


async def process_reqular_message(
    message: Message,
    sender: User,
    chat: ChatSession,
) -> None:
    """
    Обрабатывает обычные сообщения от модераторов и админов
    """
    # Преобразуем время сообщения в локальное время
    message_date = TimeZoneService.convert_to_local_time(
        dt=message.date,
    )

    msg_dto = CreateMessageDTO(
        chat_id=chat.id,
        user_id=sender.id,
        message_id=str(message.message_id),
        message_type=MessageType.MESSAGE.value,
        content_type=message.content_type.value,
        text=message.text,
        created_at=message_date,
    )

    try:
        usecase: SaveMessageUseCase = container.resolve(SaveMessageUseCase)
        await usecase.execute(message_dto=msg_dto)
    except Exception as e:
        logger.error("Error saving message: %s", str(e))


async def _get_sender_and_chat(message: Message) -> tuple[User, ChatSession]:
    """
    Получает пользователя и чат из сообщения.
    """
    # Получаем сервисы
    user_service: UserService = container.resolve(UserService)
    chat_service: ChatService = container.resolve(ChatService)

    # Получаем пользователя и чат
    username = message.from_user.username
    tg_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if not username:
        logger.warning("Пользователь без username: %s", message.from_user.id)
        return

    sender = await user_service.get_or_create(username=username, tg_id=tg_id)

    chat = await chat_service.get_or_create(
        chat_id=chat_id, title=message.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return

    return sender, chat
