import logging
import re
from typing import Optional

from aiogram import Router
from aiogram.types import Message
from punq import Container

from filters import ArchiveHashFilter
from services.chat import ArchiveBindService, ChatService

logger = logging.getLogger(__name__)
router = Router(name=__name__)

# Паттерн для поиска hash в формате ARCHIVE-{hash}
HASH_PATTERN = re.compile(r"ARCHIVE-([A-Za-z0-9_-]+)")


@router.message(ArchiveHashFilter())
async def archive_bind_message_handler(message: Message, container: Container) -> None:
    """Обработчик сообщений в архивном чате для привязки по hash."""

    # Получаем текст из сообщения или подписи
    text = message.text or message.caption or ""

    # Ищем паттерн hash (уже проверено фильтром, но для извлечения группы)
    match = HASH_PATTERN.search(text)
    if not match:
        return

    bind_hash = f"ARCHIVE-{match.group(1)}"

    logger.info(
        "Найден hash для привязки архивного чата: %s в чате %s от пользователя %s",
        bind_hash,
        message.chat.id,
        message.from_user.id if message.from_user else "unknown",
    )

    try:
        # Извлекаем данные из hash (work_chat_id, admin_tg_id)
        archive_bind_service: ArchiveBindService = container.resolve(ArchiveBindService)
        bind_data = archive_bind_service.extract_bind_data(bind_hash)

        if not bind_data:
            logger.warning("Невалидный hash: %s", bind_hash)
            admin_tg_id = (
                message.from_user.id
                if message.from_user and not message.from_user.is_bot
                else None
            )
            await _send_error_notification(
                bot=message.bot,
                user_id=admin_tg_id,
                error_text="❌ Неверный код привязки. Проверьте правильность кода.",
            )
            return

        work_chat_id, admin_tg_id = bind_data

        # Получаем информацию о текущем чате (архивном)
        archive_chat_tgid = str(message.chat.id)
        archive_chat_title = message.chat.title or f"Архивный чат {archive_chat_tgid}"

        # Привязываем архивный чат к рабочему
        chat_service: ChatService = container.resolve(ChatService)
        work_chat = await chat_service.bind_archive_chat(
            work_chat_id=work_chat_id,
            archive_chat_tgid=archive_chat_tgid,
            archive_chat_title=archive_chat_title,
        )

        if not work_chat:
            logger.error(
                "Не удалось привязать архивный чат: work_chat_id=%s, archive_chat_tgid=%s",
                work_chat_id,
                archive_chat_tgid,
            )
            notify_user_id = admin_tg_id or (
                message.from_user.id
                if message.from_user and not message.from_user.is_bot
                else None
            )
            await _send_error_notification(
                bot=message.bot,
                user_id=notify_user_id,
                error_text="❌ Ошибка при привязке архивного чата. Рабочий чат не найден.",
            )
            return

        # Отправляем уведомление об успехе (user_id из hash — админ, создавший код)
        success_text = (
            "✅ <b>Архивный чат успешно привязан</b>\n\n"
            f"📋 <b>Рабочий чат:</b> {work_chat.title}\n"
            f"📋 <b>Архивный чат:</b> {archive_chat_title}\n"
            f"🆔 <b>ID архивного чата:</b> <code>{archive_chat_tgid}</code>"
        )

        notify_user_id = admin_tg_id or (
            message.from_user.id
            if message.from_user and not message.from_user.is_bot
            else None
        )
        await _send_success_notification(
            bot=message.bot,
            user_id=notify_user_id,
            success_text=success_text,
        )

        # Удаляем сообщение с hash для безопасности
        try:
            await message.delete()
            logger.info("Сообщение с hash удалено из чата %s", archive_chat_tgid)
        except Exception as e:
            logger.warning("Не удалось удалить сообщение с hash: %s", e)

        logger.info(
            "Архивный чат %s успешно привязан к рабочему чату %s",
            archive_chat_tgid,
            work_chat_id,
        )

    except Exception as e:
        logger.error(
            "Ошибка при обработке hash для привязки архивного чата: %s",
            e,
            exc_info=True,
        )
        try:
            uid = admin_tg_id or (
                message.from_user.id
                if message.from_user and not message.from_user.is_bot
                else None
            )
        except NameError:
            uid = (
                message.from_user.id
                if message.from_user and not message.from_user.is_bot
                else None
            )
        await _send_error_notification(
            bot=message.bot,
            user_id=uid,
            error_text="❌ Произошла ошибка при привязке архивного чата. Попробуйте позже.",
        )


async def _send_success_notification(
    bot, user_id: Optional[int], success_text: str
) -> None:
    """Отправляет уведомление об успехе в приватный чат пользователя."""
    if not user_id:
        logger.warning("Не удалось отправить уведомление: user_id не указан")
        return

    try:
        await bot.send_message(chat_id=user_id, text=success_text, parse_mode="HTML")
        logger.info("Уведомление об успехе отправлено пользователю %s", user_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке уведомления об успехе пользователю %s: %s", user_id, e
        )


async def _send_error_notification(
    bot, user_id: Optional[int], error_text: str
) -> None:
    """Отправляет уведомление об ошибке в приватный чат пользователя."""
    if not user_id:
        logger.warning("Не удалось отправить уведомление об ошибке: user_id не указан")
        return

    try:
        await bot.send_message(chat_id=user_id, text=error_text, parse_mode="HTML")
        logger.info("Уведомление об ошибке отправлено пользователю %s", user_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке уведомления об ошибке пользователю %s: %s", user_id, e
        )
