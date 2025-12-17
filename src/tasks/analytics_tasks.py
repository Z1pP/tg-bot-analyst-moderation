import logging

from container import ContainerSetup, container
from repositories.message_reply_repository import MessageReplyRepository
from repositories.message_repository import MessageRepository
from repositories.reaction_repository import MessageReactionRepository
from scheduler import broker
from services.analytics_buffer_service import AnalyticsBufferService

logger = logging.getLogger(__name__)

ContainerSetup.setup()

# Константы для настройки обработки
BATCH_SIZE = 100


@broker.task
async def process_buffered_messages_task():
    """
    Задача для обработки буферизованных сообщений из Redis.
    """
    logger.debug("Начало обработки буферизованных сообщений")

    try:
        buffer_service: AnalyticsBufferService = container.resolve(
            AnalyticsBufferService
        )
        message_repository: MessageRepository = container.resolve(MessageRepository)

        messages = await buffer_service.pop_messages(BATCH_SIZE)
        if not messages:
            logger.debug("Нет сообщений для обработки")
            return

        inserted_count = await message_repository.bulk_create_messages(messages)
        # Удаляем из Redis даже если все были дубликатами
        await buffer_service.trim_messages(len(messages))

        logger.info(
            "Обработано сообщений: прочитано=%d, вставлено=%d",
            len(messages),
            inserted_count,
        )
    except Exception as e:
        logger.error(
            "Ошибка при обработке буферизованных сообщений: %s", e, exc_info=True
        )
        raise


@broker.task
async def process_buffered_reactions_task():
    """
    Задача для обработки буферизованных реакций из Redis.
    """
    logger.debug("Начало обработки буферизованных реакций")

    try:
        buffer_service: AnalyticsBufferService = container.resolve(
            AnalyticsBufferService
        )
        reaction_repository: MessageReactionRepository = container.resolve(
            MessageReactionRepository
        )

        reactions = await buffer_service.pop_reactions(BATCH_SIZE)
        if not reactions:
            logger.debug("Нет реакций для обработки")
            return

        inserted_count = await reaction_repository.bulk_add_reactions(reactions)
        # Удаляем из Redis даже если все были дубликатами
        await buffer_service.trim_reactions(len(reactions))

        logger.info(
            "Обработано реакций: прочитано=%d, вставлено=%d",
            len(reactions),
            inserted_count,
        )
    except Exception as e:
        logger.error(
            "Ошибка при обработке буферизованных реакций: %s", e, exc_info=True
        )
        raise


@broker.task
async def process_buffered_replies_task():
    """
    Задача для обработки буферизованных reply сообщений из Redis.
    """
    logger.debug("Начало обработки буферизованных reply сообщений")

    try:
        buffer_service: AnalyticsBufferService = container.resolve(
            AnalyticsBufferService
        )
        reply_repository: MessageReplyRepository = container.resolve(
            MessageReplyRepository
        )

        replies = await buffer_service.pop_replies(BATCH_SIZE)
        if not replies:
            logger.debug("Нет reply сообщений для обработки")
            return

        inserted_count = await reply_repository.bulk_create_replies(replies)
        # Удаляем из Redis даже если все были дубликатами
        await buffer_service.trim_replies(len(replies))

        logger.info(
            "Обработано reply сообщений: прочитано=%d, вставлено=%d",
            len(replies),
            inserted_count,
        )
    except Exception as e:
        logger.error(
            "Ошибка при обработке буферизованных reply сообщений: %s", e, exc_info=True
        )
        raise
