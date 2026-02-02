from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def users_chats_settings_ikb(has_tracking: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура настроек пользователей и чатов"""
    builder = InlineKeyboardBuilder()

    if has_tracking:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.USERS_MENU,
                callback_data=CallbackData.User.SHOW_MENU,
            ),
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.CHATS_MENU,
                callback_data=CallbackData.Chat.SHOW_MENU,
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.RESET_SETTINGS,
                callback_data=CallbackData.UserAndChatsSettings.RESET_SETTINGS,
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.FIRST_TIME_SETTINGS,
                callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS,
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )

    return builder.as_markup()


def first_time_setup_ikb() -> InlineKeyboardMarkup:
    """Клавиатура выбора при первоначальной настройке (начать настройку или вернуться в меню)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.CONTINUE_SETTINGS,
            callback_data=CallbackData.UserAndChatsSettings.CONTINUE_SETTINGS,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.UserAndChatsSettings.SHOW_MENU,
        ),
        width=2,
    )

    return builder.as_markup()


def first_time_work_hours_ikb(all_filled: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура настройки времени в визарде первоначальной настройки.
    Кнопка «Сохранить и закончить» показывается только при all_filled=True.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_WORK_START,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_WORK_START,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_WORK_END,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_WORK_END,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_TOLERANCE,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_TOLERANCE,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Chat.CHANGE_BREAKS_TIME,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_BREAKS_TIME,
        ),
    )
    if all_filled:
        builder.row(
            InlineKeyboardButton(
                text=InlineButtons.UserAndChatsSettings.SAVE_AND_FINISH_SETUP,
                callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SAVE_AND_FINISH,
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.UserAndChatsSettings.SHOW_MENU,
        ),
    )
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


def first_time_setup_success_ikb(chat_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура после успешного завершения первоначальной настройки.
    Две кнопки по одной в ряд: Перейти в Настройки чата, Вернуться.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.GO_TO_CHAT_SETTINGS,
            callback_data=f"{CallbackData.Chat.PREFIX_CHAT}{chat_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.SHOW_MENU,
        ),
    )
    return builder.as_markup()


def first_time_cancel_time_input_ikb() -> InlineKeyboardMarkup:
    """Клавиатура отмены ввода одного поля времени (возврат в меню времени)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_CANCEL_TIME_INPUT,
        ),
    )
    return builder.as_markup()


def confirm_reset_ikb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения сброса настроек"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.YES,
            callback_data=CallbackData.UserAndChatsSettings.CONFIRM_RESET,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.NO,
            callback_data=CallbackData.UserAndChatsSettings.CANCEL_RESET,
        ),
    )

    return builder.as_markup()


def reset_success_ikb() -> InlineKeyboardMarkup:
    """Клавиатура успешного сброса настроек"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserAndChatsSettings.START_FIRST_TIME_SETTINGS,
            callback_data=CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.UserAndChatsSettings.SHOW_MENU,
        )
    )

    return builder.as_markup()
