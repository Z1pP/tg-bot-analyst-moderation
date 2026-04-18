"""Инлайн-клавиатура уведомления автомодерации в архивном чате."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from utils.automoderation import encode_automod_block_callback


def automoderation_alert_ikb(
    work_chat_tgid: str, violator_user_id: int
) -> InlineKeyboardMarkup:
    """Кнопки «Заблокировать» и «Отменить» для карточки о спамере."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.AUTO_MODERATION_BLOCK,
            callback_data=encode_automod_block_callback(
                work_chat_tgid, violator_user_id
            ),
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.AUTO_MODERATION_CANCEL,
            callback_data=CallbackData.AutoModeration.CANCEL,
        ),
    )
    return builder.as_markup()
