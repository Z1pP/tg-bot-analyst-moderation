import logging

from aiogram import Router
from aiogram.types import Message
from punq import Container

from dto.automoderation import CheckAndRunAutoModerationDTO
from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO
from dto.time_dto import ConvertToLocalTimeDTO
from models.message import MessageType
from usecases.automoderation import CheckAndRunAutoModerationUseCase
from usecases.message import (
    SaveMessageUseCase,
    SaveReplyMessageUseCase,
)
from usecases.time import ConvertToLocalTimeUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _run_automoderation_if_needed(message: Message, container: Container) -> None:
    """Передаёт текстовое сообщение в use case автомодерации."""
    if not message.text or message.from_user is None:
        return

    usecase: CheckAndRunAutoModerationUseCase = container.resolve(
        CheckAndRunAutoModerationUseCase
    )
    await usecase.execute(
        CheckAndRunAutoModerationDTO(
            chat_tgid=str(message.chat.id),
            chat_title=message.chat.title,
            username=message.from_user.username,
            user_tg_id=message.from_user.id,
            message_id=message.message_id,
            message_text=message.text,
        )
    )


def _get_message_type(message: Message) -> MessageType:
    if message.reply_to_message:
        return MessageType.REPLY
    else:
        return MessageType.MESSAGE


@router.message()
async def group_message_handler(message: Message, container: Container) -> None:
    """
    Сохраняет все сообщения и ответы от всех пользователей для построения метрик.
    """
    if message.from_user is None or message.from_user.is_bot:
        return

    # sender, chat = await _get_sender_and_chat(message, container)
    # if not sender or not chat:
    #     return

    msg_type = _get_message_type(message)

    if msg_type == MessageType.REPLY:
        await process_reply_message(message, container)
    else:
        await process_message(message, container)


async def process_reply_message(
    message: Message,
    container: Container,
) -> None:
    """
    Сохраняет reply-сообщения и связь с оригинальным сообщением.
    """
    reply_to_message = message.reply_to_message
    if message.from_user is None or reply_to_message is None:
        return
    convert_uc: ConvertToLocalTimeUseCase = container.resolve(ConvertToLocalTimeUseCase)
    message_date = convert_uc.execute(ConvertToLocalTimeDTO(dt=message.date))
    reply_to_message_date = convert_uc.execute(
        ConvertToLocalTimeDTO(dt=reply_to_message.date)
    )
    if message_date is None or reply_to_message_date is None:
        return

    # Создаем DTO для сохранения сообщения
    msg_dto = CreateMessageDTO(
        chat_tgid=str(message.chat.id),
        user_tgid=str(message.from_user.id),
        user_username=message.from_user.username,
        message_id=str(message.message_id),
        message_type=MessageType.REPLY.value,
        content_type=message.content_type,
        text=message.text,
        created_at=message_date,
    )

    try:
        # Сохраняем reply как обычное сообщение
        message_usecase: SaveMessageUseCase = container.resolve(SaveMessageUseCase)
        await message_usecase.execute(message_dto=msg_dto)

        # Создаем ссылку на оригинальное сообщение
        original_message_url = _get_original_message_url(message)

        # DTO для связи reply с оригинальным сообщением
        # Используем message_id (Telegram string) вместо DB id, так как сообщение еще не сохранено
        reply_dto = CreateMessageReplyDTO(
            chat_tgid=str(message.chat.id),
            reply_user_tgid=str(message.from_user.id),
            reply_user_username=message.from_user.username,
            original_message_url=original_message_url,
            reply_message_id=0,  # Временное значение, будет заменено в воркере по message_id
            original_message_date=message_date,
            reply_message_date=reply_to_message_date,
            response_time_seconds=int(
                (message_date - reply_to_message_date).total_seconds()
            ),
            reply_message_id_str=str(message.message_id),
        )

        # Сохраняем связь в MessageReply
        reply_usecase: SaveReplyMessageUseCase = container.resolve(
            SaveReplyMessageUseCase
        )
        await reply_usecase.execute(reply_message_dto=reply_dto)
        await _run_automoderation_if_needed(message, container)
    except Exception as e:
        logger.error("Ошибка сохранения reply сообщения: %s", str(e))


async def process_message(
    message: Message,
    container: Container,
) -> None:
    """
    Сохраняет обычные сообщения от всех пользователей.
    """
    if message.from_user is None:
        return
    convert_uc: ConvertToLocalTimeUseCase = container.resolve(ConvertToLocalTimeUseCase)
    message_date = convert_uc.execute(ConvertToLocalTimeDTO(dt=message.date))
    if message_date is None:
        return

    msg_dto = CreateMessageDTO(
        chat_tgid=str(message.chat.id),
        user_tgid=str(message.from_user.id),
        user_username=message.from_user.username,
        message_id=str(message.message_id),
        message_type=MessageType.MESSAGE.value,
        content_type=message.content_type,
        text=message.text,
        created_at=message_date,
    )

    try:
        usecase: SaveMessageUseCase = container.resolve(SaveMessageUseCase)
        await usecase.execute(message_dto=msg_dto)
        await _run_automoderation_if_needed(message, container)
        # client_service: ApiClient = container.resolve(ApiClient)
        # await client_service.message.create_message(msg_dto)

    except Exception as e:
        logger.error("Ошибка сохранения сообщения: %s", str(e))


def _get_original_message_url(message: Message) -> str:
    """
    Генерирует ссылку на оригинальное сообщение.
    """
    reply_to_message = message.reply_to_message
    if reply_to_message is None:
        return ""
    chat_id = str(message.chat.id)
    message_id = reply_to_message.message_id

    if chat_id.startswith("-100"):
        # Супергруппы: убираем -100
        clean_chat_id = chat_id[4:]
    elif chat_id.startswith("-"):
        # Обычные группы: убираем только -
        clean_chat_id = chat_id[1:]
    else:
        # Личные чаты или каналы
        clean_chat_id = chat_id

    return f"https://t.me/c/{clean_chat_id}/{message_id}"
