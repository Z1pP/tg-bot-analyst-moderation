from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import Dialog, InlineButtons
from constants.callback import CallbackData


def punishment_setting_ikb() -> InlineKeyboardMarkup:
    """Клавиатура настройки наказаний"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.PUNISHMENT_CREATE_NEW,
            callback_data=CallbackData.Chat.PUNISHMENT_CREATE_NEW,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.PUNISHMENT_SET_DEFAULT,
            callback_data=CallbackData.Chat.PUNISHMENT_SET_DEFAULT,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
        )
    )

    builder.adjust(2, 1)

    return builder.as_markup()


def punishment_action_ikb() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа наказания для ступени"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.ACTION_WARNING,
            callback_data=CallbackData.Chat.PUNISH_ACTION_WARNING,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.ACTION_MUTE,
            callback_data=CallbackData.Chat.PUNISH_ACTION_MUTE,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.ACTION_BAN,
            callback_data=CallbackData.Chat.PUNISH_ACTION_BAN,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Chat.PUNISHMENT_SETTING,
        )
    )

    builder.adjust(3, 1)

    return builder.as_markup()


def punishment_next_step_ikb() -> InlineKeyboardMarkup:
    """Клавиатура после добавления ступени"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.STEP_ADD_MORE,
            callback_data=CallbackData.Chat.PUNISH_STEP_NEXT,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.STEP_SAVE_LADDER,
            callback_data=CallbackData.Chat.PUNISH_STEP_SAVE,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.STEP_CANCEL,
            callback_data=CallbackData.Chat.PUNISH_STEP_CANCEL,
        )
    )

    return builder.as_markup()


def cancel_punishment_creation_ikb() -> InlineKeyboardMarkup:
    """Клавиатура отмены создания лестницы наказаний"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=Dialog.Punishment.STEP_CANCEL,
            callback_data=CallbackData.Chat.PUNISH_STEP_CANCEL,
        )
    )
    return builder.as_markup()
