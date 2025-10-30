from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons


def message_action_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с действиями над сообщением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.DELETE,
            callback_data="delete_message",
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.REPLY,
            callback_data="reply_message",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.CANCEL,
            callback_data="cancel",
        ),
    )
    return builder.as_markup()


def confirm_delete_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.CONFIRM_DELETE,
            callback_data="delete_message_confirm",
        ),
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.CANCEL,
            callback_data="delete_message_cancel",
        ),
    )
    return builder.as_markup()


def send_message_ikb() -> types.InlineKeyboardMarkup:
    """Клавиатура с кнопкой отправки сообщения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=InlineButtons.MessageActions.SEND_MESSAGE,
            callback_data="send_message_to_chat",
        ),
    )
    return builder.as_markup()
