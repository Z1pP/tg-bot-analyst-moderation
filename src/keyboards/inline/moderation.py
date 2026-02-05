"""Модуль инлайн-клавиатур для раздела модерации.

Содержит функции для создания клавиатур управления пользователями,
выбора причин наказания и навигации по меню модерации.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def no_reason_ikb() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой для пропуска ввода причины.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой 'Без причины'.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Moderation.NO_REASON,
            callback_data=InlineButtons.Moderation.NO_REASON,
        )
    )
    return builder.as_markup()


def moderation_menu_ikb() -> InlineKeyboardMarkup:
    """Создает главное меню раздела модерации.

    Включает кнопки для выдачи предупреждений, блокировки, амнистии,
    управления чатами и возврата в главное меню.

    Returns:
        InlineKeyboardMarkup: Разметка главного меню модерации.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Moderation.WARN_USER,
            callback_data=InlineButtons.Moderation.WARN_USER,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Moderation.BLOCK_USER,
            callback_data=InlineButtons.Moderation.BLOCK_USER,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Moderation.AMNESTY,
            callback_data=InlineButtons.Moderation.AMNESTY,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Chat.MANAGEMENT,
            callback_data=CallbackData.Chat.MANAGEMENT,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Menu.MAIN_MENU,
        ),
    )

    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


def back_to_moderation_menu_ikb() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой отмены и возврата в меню модерации.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой 'Отмена'.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Moderation.SHOW_MENU,
        )
    )
    return builder.as_markup()


def amnesty_actions_ikb() -> InlineKeyboardMarkup:
    """Создает меню выбора действий для амнистии пользователя.

    Включает опции отмены варна, размута, разбана и кнопку возврата.

    Returns:
        InlineKeyboardMarkup: Клавиатура с действиями амнистии.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Moderation.CANCEL_WARN,
            callback_data=InlineButtons.Moderation.CANCEL_WARN,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Moderation.UNMUTE,
            callback_data=InlineButtons.Moderation.UNMUTE,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Moderation.UNBAN,
            callback_data=InlineButtons.Moderation.UNBAN,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Moderation.SHOW_MENU,
        ),
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()
