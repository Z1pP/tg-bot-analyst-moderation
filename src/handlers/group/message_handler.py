import logging

from aiogram import Router
from aiogram.types import Message

from container import container
from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO
from filters.group_filter import GroupTypeFilter
from models import ChatSession, User
from models.message import MessageType
from usecases.message import ProcessMessageUseCase, ProcessReplyMessageUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _get_message_type(message: Message) -> MessageType:
    if message.reply_to_message:
        return MessageType.REPLY
    else:
        return MessageType.MESSAGE


@router.message(GroupTypeFilter())
async def group_message_handler(message: Message, **data):
    """
    Обрабатывет сообщения которые приходит только от модераторов чата
    """
    sender: User = data.get("sender")
    chat: ChatSession = data.get("chat")

    if not sender or not chat:
        return

    msg_type = _get_message_type(message=message)

    if msg_type == MessageType.REPLY:
        await process_moderator_reply(message=message, sender=sender, chat=chat)
    else:
        await precess_moderator_message(message=message, sender=sender, chat=chat)


async def process_moderator_reply(message: Message, sender: User, chat: ChatSession):
    """
    Обрабатывает reply-сообщения модераторов.
    Сохраняет reply как обычное сообщение, а затем создаёт связь в MessageReply.
    """
    # DTO для сохранения сообщения
    msg_dto = CreateMessageDTO(
        chat_id=chat.id,
        user_id=sender.id,
        message_id=str(message.message_id),
        message_type=MessageType.REPLY.value,
        content_type=message.content_type,
        text=message.text,
    )

    # Получаем use case для обработки сообщений
    message_usecase: ProcessMessageUseCase = container.resolve(ProcessMessageUseCase)
    reply_usecase: ProcessReplyMessageUseCase = container.resolve(
        ProcessReplyMessageUseCase
    )

    try:
        # Сохраняем reply как обычное сообщение
        saved_message = await message_usecase.execute(message_dto=msg_dto)

        # DTO для связи reply с оригинальным сообщением
        reply_dto = CreateMessageReplyDTO(
            chat_id=chat.id,
            original_message_url=message.reply_to_message.text,  # ID оригинального сообщения
            reply_message_id=saved_message.id,  # ID сохранённого reply-сообщения
            reply_user_id=sender.id,
            original_message_date=message.reply_to_message.date,
            reply_message_date=message.date,
            response_time_seconds=(
                (message.date - message.reply_to_message.date).total_seconds()
            ),
        )

        # Сохраняем связь в MessageReply
        await reply_usecase.execute(reply_message_dto=reply_dto)

        await message.answer("Сообщение сохранено")
    except Exception as e:
        logger.error("Error saving reply message: %s", str(e))
        await message.answer("Ошибка при сохранении сообщения")


async def precess_moderator_message(message: Message, sender: User, chat: ChatSession):
    """Обрабатывает сообщения которые не являются reply"""
    msg_dto = CreateMessageDTO(
        chat_id=chat.id,
        user_id=sender.id,
        message_id=str(message.message_id),
        message_type=MessageType.MESSAGE.value,
        content_type=message.content_type,
        text=message.text,
    )

    usecase: ProcessMessageUseCase = container.resolve(ProcessMessageUseCase)

    try:
        await usecase.execute(message_dto=msg_dto)
        await message.answer("Сообщение сохранено")
    except Exception as e:
        logger.error("Error saving message: %s", str(e))
        await message.answer("Ошибка при сохранении сообщения")
