import logging
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants import Dialog
from constants.callback import CallbackData

logger = logging.getLogger(__name__)
router = Router(name="group_common_router")


async def send_notification(
    bot: Bot,
    chat_id: int,
    message_text: str,
    parse_mode: str = "HTML",
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Отправляет уведомление пользователю."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
        logger.info(f"Отправлено сообщения в чат с chat_id={chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в чат с chat_id={chat_id}: {e}")


async def send_permission_error(
    bot: Bot,
    admin_telegram_id: int,
    admin_username: str,
    bot_status_is_member: bool,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    error_text: Optional[str] = None,
) -> None:
    """Отправляет сообщение об ошибке прав в приватный чат"""
    try:
        logger.debug(
            f"Отправка уведомления об ошибке прав админу {admin_username} (ID: {admin_telegram_id})"
        )

        if not error_text:
            if not bot_status_is_member:
                error_text = Dialog.Chat.ERROR_ADD_CHAT_NOT_MEMBER
            else:
                error_text = Dialog.Chat.ERROR_ADD_CHAT_INSUFFICIENT_PERMISSIONS

        await bot.send_message(
            chat_id=admin_telegram_id,
            text=error_text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        logger.info(f"Уведомление об ошибке прав отправлено админу {admin_username}")

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")


@router.callback_query(F.data == CallbackData.Menu.HIDE_NOTIFICATION)
async def close_notification_handler(callback: CallbackQuery) -> None:
    """Обработчик закрытия уведомления."""
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при закрытии уведомления: {e}")
        await callback.answer()
