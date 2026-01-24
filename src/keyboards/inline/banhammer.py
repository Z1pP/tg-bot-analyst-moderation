from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData

block_actions = InlineButtons.BlockButtons()


def no_reason_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Без причины'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=block_actions.NO_REASON,
            callback_data=block_actions.NO_REASON,
        )
    )
    return builder.as_markup()


def moderation_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с действия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=block_actions.AMNESTY,
            callback_data=block_actions.AMNESTY,
        ),
        InlineKeyboardButton(
            text=block_actions.WARN_USER,
            callback_data=block_actions.WARN_USER,
        ),
        InlineKeyboardButton(
            text=block_actions.BLOCK_USER,
            callback_data=block_actions.BLOCK_USER,
        ),
    )
    builder.adjust(1, 2)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.User.COME_BACK,
            callback_data=CallbackData.Menu.MAIN_MENU,
        )
    )
    return builder.as_markup()


def back_to_block_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в меню блокировок"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=block_actions.BACK_TO_BLOCK_MENU,
            callback_data=block_actions.BACK_TO_BLOCK_MENU,
        )
    )
    return builder.as_markup()


def amnesty_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура с действиями по амнистии"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=block_actions.CANCEL_WARN,
            callback_data=block_actions.CANCEL_WARN,
        ),
        InlineKeyboardButton(
            text=block_actions.UNMUTE,
            callback_data=block_actions.UNMUTE,
        ),
        InlineKeyboardButton(
            text=block_actions.UNBAN,
            callback_data=block_actions.UNBAN,
        ),
        InlineKeyboardButton(
            text=block_actions.BACK_TO_BLOCK_MENU,
            callback_data=block_actions.BACK_TO_BLOCK_MENU,
        ),
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()
