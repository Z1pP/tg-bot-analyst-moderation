from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def punishment_setting_ikb() -> InlineKeyboardMarkup:
    """Клавиатура настройки наказаний"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.PUNISHMENT_CREATE_NEW,
            callback_data=CallbackData.Chat.PUNISHMENT_CREATE_NEW,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.PUNISHMENT_SET_DEFAULT,
            callback_data=CallbackData.Chat.PUNISHMENT_SET_DEFAULT,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ChatButtons.BACK_TO_SELECT_ACTION,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        )
    )

    return builder.as_markup()


def punishment_action_ikb() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа наказания для ступени"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Предупреждение",
            callback_data="punish_action_warning",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Мут",
            callback_data="punish_action_mute",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Бан",
            callback_data="punish_action_ban",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="punish_action_cancel",
        )
    )

    return builder.as_markup()


def punishment_next_step_ikb() -> InlineKeyboardMarkup:
    """Клавиатура после добавления ступени"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить еще",
            callback_data="punish_step_next",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Сохранить лестницу",
            callback_data="punish_step_save",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="punish_step_cancel",
        )
    )

    return builder.as_markup()
