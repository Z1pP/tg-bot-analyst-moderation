from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


from constants import InlineButtons

block_actions = InlineButtons.BlockButtons()


def confirm_action_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=block_actions.CONFIRM_ACTION,
            callback_data=block_actions.CONFIRM_ACTION,
        ),
        InlineKeyboardButton(
            text=block_actions.CANCEL_ACTION,
            callback_data=block_actions.CANCEL_ACTION,
        ),
    )

    return builder.as_markup()
