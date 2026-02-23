import asyncio
import logging

from container import ContainerSetup, container
from scheduler import broker
from services.messaging.bot_message_service import BotMessageService

logger = logging.getLogger(__name__)

ContainerSetup.setup()


@broker.task
async def kick_unverified_member_task(
    chat_id: int,
    message_id: int,
    user_id: int,
    delay_seconds: int = 3600,
) -> None:
    """
    Задача для кика непроверенного участника по истечении времени.

    Если сообщение с кнопкой верификации ещё существует (пользователь не нажал кнопку),
    удаляет его и кикает пользователя (бан + разбан = кик без постоянного бана).
    Если сообщение уже удалено (пользователь прошёл верификацию), пропускает кик.

    Args:
        chat_id: ID чата
        message_id: ID приветственного сообщения с кнопкой
        user_id: ID пользователя, которого нужно кикнуть при неудаче
        delay_seconds: Задержка перед проверкой в секундах
    """
    if delay_seconds > 0:
        logger.info(
            "Ожидание %s секунд перед проверкой верификации пользователя %s в чате %s",
            delay_seconds,
            user_id,
            chat_id,
        )
        await asyncio.sleep(delay_seconds)

    logger.info(
        "Проверка верификации пользователя %s в чате %s (сообщение %s)",
        user_id,
        chat_id,
        message_id,
    )

    try:
        bot_message_service: BotMessageService = container.resolve(BotMessageService)

        # Пытаемся удалить сообщение с кнопкой верификации.
        # Если True — сообщение существовало, пользователь не верифицировался → кикаем.
        # Если False — сообщение уже удалено, пользователь прошёл верификацию → пропускаем.
        message_deleted = await bot_message_service.delete_message_from_chat(
            chat_id=chat_id,
            message_id=message_id,
        )

        if not message_deleted:
            logger.info(
                "Сообщение %s уже удалено — пользователь %s прошёл верификацию, кик пропущен",
                message_id,
                user_id,
            )
            return

        logger.info(
            "Пользователь %s не прошёл верификацию за отведённое время, кикаем из чата %s",
            user_id,
            chat_id,
        )

        kicked = await bot_message_service.kick_chat_member(
            chat_tg_id=chat_id,
            user_tg_id=user_id,
        )

        if kicked:
            logger.info(
                "Пользователь %s успешно кикнут из чата %s",
                user_id,
                chat_id,
            )
        else:
            logger.warning(
                "Не удалось кикнуть пользователя %s из чата %s",
                user_id,
                chat_id,
            )

    except Exception as e:
        logger.error(
            "Ошибка при кике незверифицированного пользователя %s из чата %s: %s",
            user_id,
            chat_id,
            e,
            exc_info=True,
        )


@broker.task
async def delete_message_from_chat(
    chat_id: int,
    message_id: int,
    delay_seconds: int = 1800,
) -> None:
    """
    Задача для удаления сообщения бота через заданное время.

    Args:
        chat_id: ID чата
        message_id: ID сообщения
        delay_seconds: Задержка перед удалением в секундах (по умолчанию 30 минут)
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
        "Выполнение задачи удаления сообщения: chat_id=%s, message_id=%s",
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
            "Сообщение успешно удалено: chat_id=%s, message_id=%s",
            chat_id,
            message_id,
        )
    except Exception as e:
        logger.error(
            "Ошибка при удалении сообщения chat_id=%s, message_id=%s: %s",
            chat_id,
            message_id,
            e,
            exc_info=True,
        )
        # Не делаем raise, чтобы не перезапускать задачу, если сообщение уже удалено или бот выгнан
