import logging

from aiogram import Router
from aiogram.types import Message

from container import container
from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO
from filters.group_filter import GroupTypeFilter
from models import ChatSession, User
from models.message import MessageType
from services.chat import ChatService
from services.time_service import TimeZoneService
from services.user import UserService
from usecases.message import ProcessMessageUseCase, ProcessReplyMessageUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _get_message_type(message: Message) -> MessageType:
    if message.reply_to_message:
        return MessageType.REPLY
    else:
        return MessageType.MESSAGE


@router.message(GroupTypeFilter())
async def group_message_handler(message: Message):
    """
    Обрабатывет сообщения которые приходит только от модераторов чата
    """
    # Сообщения от ботов не сохраняются
    if message.from_user.is_bot:
        return

    sender, chat = await _get_sender_and_chat(message=message)

    # Обрабатываем сообщение в зависимости от типа
    msg_type = _get_message_type(message=message)
    if msg_type == MessageType.REPLY:
        await process_moderator_reply(
            message=message,
            sender=sender,
            chat=chat,
        )
    else:
        await process_moderator_message(
            message=message,
            sender=sender,
            chat=chat,
        )


async def process_moderator_reply(message: Message, sender, chat):
    """
    Обрабатывает reply-сообщения модераторов.
    Сохраняет reply как обычное сообщение, а затем создаёт связь в MessageReply.
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
        message_usecase = container.resolve(ProcessMessageUseCase)
        saved_message = await message_usecase.execute(message_dto=msg_dto)

        # Создаем ссылку на оригинальное сообщение
        original_message_url = f"https://t.me/c/{chat.chat_id.lstrip('-')}/{message.reply_to_message.message_id}"

        # DTO для связи reply с оригинальным сообщением
        reply_dto = CreateMessageReplyDTO(
            chat_id=chat.id,
            original_message_url=original_message_url,
            reply_message_id=saved_message.id,
            reply_user_id=sender.id,
            response_time_seconds=(
                message_date - reply_to_message_date
            ).total_seconds(),
        )

        # Сохраняем связь в MessageReply
        reply_usecase = container.resolve(ProcessReplyMessageUseCase)
        await reply_usecase.execute(reply_message_dto=reply_dto)
    except Exception as e:
        logger.error("Error saving reply message: %s", str(e))


async def process_moderator_message(message: Message, sender, chat):
    """
    Обрабатывает сообщения которые не являются reply
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
        usecase = container.resolve(ProcessMessageUseCase)
        await usecase.execute(message_dto=msg_dto)
    except Exception as e:
        logger.error("Error saving message: %s", str(e))


async def _get_sender_and_chat(message: Message) -> tuple[User, ChatSession]:
    """
    Получает пользователя и чат из сообщения.
    """
    # Получаем сервисы
    user_service = container.resolve(UserService)
    chat_service = container.resolve(ChatService)

    # Получаем пользователя и чат
    username = message.from_user.username
    chat_id = str(message.chat.id)

    if not username:
        logger.warning("Пользователь без username: %s", message.from_user.id)
        return

    sender = await user_service.get_user(username)
    if not sender:
        logger.warning("Пользователь не найден в базе данных: %s", username)
        return

    chat = await chat_service.get_or_create_chat(
        chat_id=chat_id, title=message.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return

    return sender, chat
