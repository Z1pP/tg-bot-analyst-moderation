from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def confirm_action_ikb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия амнистии.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками подтверждения и отмены действия амнистии.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.YES,
            callback_data=CallbackData.Moderation.CONFIRM_ACTION,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.NO,
            callback_data=CallbackData.Moderation.CANCEL_ACTION,
        ),
    )

    return builder.as_markup()
