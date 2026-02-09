import asyncio
import logging

from container import ContainerSetup, container
from scheduler import broker
from services.messaging.bot_message_service import BotMessageService

logger = logging.getLogger(__name__)

ContainerSetup.setup()


@broker.task
async def delete_welcome_message_task(
    chat_id: int,
    message_id: int,
    delay_seconds: int = 3600,
):
    """
    Задача для удаления приветственного сообщения через заданное время.

    Args:
        chat_id: ID чата
        message_id: ID сообщения
        delay_seconds: Задержка перед удалением в секундах
    """
    if delay_seconds > 0:
        logger.info(
            "Ожидание %s секунд перед удалением сообщения %s в чате %s",
            delay_seconds,
            message_id,
            chat_id,
        )
        await asyncio.sleep(delay_seconds)

    logger.info(
        "Выполнение задачи удаления приветственного сообщения: chat_id=%s, message_id=%s",
        chat_id,
        message_id,
    )

    try:
        bot_message_service: BotMessageService = container.resolve(BotMessageService)
        await bot_message_service.delete_message_from_chat(
            chat_id=chat_id,
            message_id=message_id,
        )
        logger.info(
            "Приветственное сообщение успешно удалено: chat_id=%s, message_id=%s",
            chat_id,
            message_id,
        )
    except Exception as e:
        logger.error(
            "Ошибка при удалении приветственного сообщения chat_id=%s, message_id=%s: %s",
            chat_id,
            message_id,
            e,
            exc_info=True,
        )
        # Не делаем raise, чтобы не перезапускать задачу, если сообщение уже удалено или бот выгнан
