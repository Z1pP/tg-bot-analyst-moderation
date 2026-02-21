import logging
import re
from typing import Any, Optional

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from punq import Container

from dto.chat_dto import BindArchiveChatDTO
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from filters import ArchiveHashFilter
from models import ChatSession
from usecases.archive import BindArchiveChatUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)

# Паттерн для поиска hash в формате ARCHIVE-{hash}
HASH_PATTERN = re.compile(r"ARCHIVE-([A-Za-z0-9_-]+)")


def _resolve_notify_user_id(message: Message, admin_tg_id: Optional[int]) -> Optional[int]:
    """Возвращает ID пользователя для уведомления: приоритет admin_tg_id, иначе отправитель сообщения (не бот)."""
    if admin_tg_id is not None:
        return admin_tg_id
    if message.from_user and not message.from_user.is_bot:
        return message.from_user.id
    return None


def _extract_bind_hash_from_message(message: Message) -> Optional[str]:
    """Извлекает bind_hash из текста/подписи сообщения. None если не найден."""
    text = message.text or message.caption or ""
    match = HASH_PATTERN.search(text)
    if not match:
        return None
    return f"ARCHIVE-{match.group(1)}"


async def _execute_bind(
    container: Container,
    bind_hash: str,
    archive_chat_tgid: str,
    archive_chat_title: str,
) -> Optional[tuple[int, Optional[int], Optional[ChatSession]]]:
    """Выполняет привязку архивного чата. Возвращает (work_chat_id, admin_tg_id, work_chat) или None."""
    bind_uc: BindArchiveChatUseCase = container.resolve(BindArchiveChatUseCase)
    return await bind_uc.execute(
        BindArchiveChatDTO(
            bind_hash=bind_hash,
            archive_chat_tgid=archive_chat_tgid,
            archive_chat_title=archive_chat_title,
        )
    )


async def _try_delete_message_with_hash(message: Message, archive_chat_tgid: str) -> None:
    """Удаляет сообщение с hash из чата для безопасности. Ошибки API логируются, не прерывают поток."""
    try:
        await message.delete()
        logger.info("Сообщение с hash удалено из чата %s", archive_chat_tgid)
    except TelegramAPIError as e:
        logger.warning("Не удалось удалить сообщение с hash в чате %s: %s", archive_chat_tgid, e)


@router.message(ArchiveHashFilter())
async def archive_bind_message_handler(message: Message, container: Container) -> None:
    """Обработчик сообщений в архивном чате для привязки по hash."""
    admin_tg_id: Optional[int] = None

    bind_hash = _extract_bind_hash_from_message(message)
    if not bind_hash:
        return

    logger.info(
        "Найден hash для привязки архивного чата: %s в чате %s от пользователя %s",
        bind_hash,
        message.chat.id,
        message.from_user.id if message.from_user else "unknown",
    )

    archive_chat_tgid = str(message.chat.id)
    archive_chat_title = message.chat.title or f"Архивный чат {archive_chat_tgid}"

    try:
        result = await _execute_bind(
            container=container,
            bind_hash=bind_hash,
            archive_chat_tgid=archive_chat_tgid,
            archive_chat_title=archive_chat_title,
        )

        if result is None:
            logger.warning("Невалидный hash: %s", bind_hash)
            await _send_private_notification(
                bot=message.bot,
                user_id=_resolve_notify_user_id(message, None),
                text="❌ Неверный код привязки. Проверьте правильность кода.",
                is_success=False,
            )
            return

        work_chat_id, admin_tg_id, work_chat = result

        if work_chat is None:
            logger.error(
                "Не удалось привязать архивный чат: work_chat_id=%s, archive_chat_tgid=%s",
                work_chat_id,
                archive_chat_tgid,
            )
            await _send_private_notification(
                bot=message.bot,
                user_id=_resolve_notify_user_id(message, admin_tg_id),
                text="❌ Ошибка при привязке архивного чата. Рабочий чат не найден.",
                is_success=False,
            )
            return

        success_text = (
            "✅ <b>Архивный чат успешно привязан</b>\n\n"
            f"📋 <b>Рабочий чат:</b> {work_chat.title}\n"
            f"📋 <b>Архивный чат:</b> {archive_chat_title}\n"
            f"🆔 <b>ID архивного чата:</b> <code>{archive_chat_tgid}</code>"
        )
        await _send_private_notification(
            bot=message.bot,
            user_id=_resolve_notify_user_id(message, admin_tg_id),
            text=success_text,
            is_success=True,
        )

        await _try_delete_message_with_hash(message, archive_chat_tgid)

        logger.info(
            "Архивный чат %s успешно привязан к рабочему чату %s",
            archive_chat_tgid,
            work_chat_id,
        )

    except BotBaseException as e:
        notify_user_id = _resolve_notify_user_id(message, admin_tg_id)
        await _send_private_notification(
            bot=message.bot,
            user_id=notify_user_id,
            text=e.get_user_message(),
            is_success=False,
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка при обработке hash для привязки архивного чата.",
            "❌ Произошла ошибка при привязке архивного чата. Попробуйте позже.",
            e,
            logger,
        )


async def _send_private_notification(
    bot: Any,
    user_id: Optional[int],
    text: str,
    *,
    is_success: bool = True,
) -> None:
    """Отправляет уведомление в приватный чат пользователя (успех или ошибка)."""
    if not user_id:
        logger.warning(
            "Не удалось отправить уведомление: user_id не указан"
        )
        return

    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
        log_template = "Уведомление об успехе отправлено пользователю %s" if is_success else "Уведомление об ошибке отправлено пользователю %s"
        logger.info(log_template, user_id)
    except TelegramAPIError as e:
        logger.error(
            "Ошибка при отправке уведомления пользователю %s: %s", user_id, e,
            exc_info=True,
        )
        raise
