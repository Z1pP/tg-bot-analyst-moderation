from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def confirm_humanity_verification_ikb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения верификации человечности"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Antibot.CONFIRM_HUMANITY,
            callback_data=f"{CallbackData.Antibot.CONFIRM_HUMANITY_PREFIX}{user_id}",
        ),
    )
    return builder.as_markup()
