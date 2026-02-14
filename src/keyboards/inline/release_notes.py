"""Клавиатуры сценария рассылки релизной заметки (ввод текста → язык → подтверждение)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData


def broadcast_step1_ikb() -> InlineKeyboardMarkup:
    """Шаг 1: ввод текста. Одна кнопка «Вернуться» → ROOT.MENU."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Root.SHOW_MENU,
        )
    )
    return builder.as_markup()


def broadcast_step2_ikb() -> InlineKeyboardMarkup:
    """Шаг 2: выбор языка. RU, EN, Изменить текст заметки, Отмена."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="RU",
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_BROADCAST_LANG}ru",
        ),
        InlineKeyboardButton(
            text="EN",
            callback_data=f"{CallbackData.ReleaseNotes.PREFIX_BROADCAST_LANG}en",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.ReleaseNotes.CHANGE_NOTE_TEXT,
            callback_data=CallbackData.ReleaseNotes.CHANGE_NOTE_TEXT,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.CANCEL,
            callback_data=CallbackData.Root.SHOW_MENU,
        )
    )
    return builder.as_markup()


def broadcast_confirm_ikb() -> InlineKeyboardMarkup:
    """Подтверждение рассылки: Да / Нет."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.YES,
            callback_data=CallbackData.ReleaseNotes.CONFIRM_BROADCAST_YES,
        ),
        InlineKeyboardButton(
            text=InlineButtons.Common.NO,
            callback_data=CallbackData.Root.SHOW_MENU,
        ),
    )
    return builder.as_markup()


def broadcast_success_ikb() -> InlineKeyboardMarkup:
    """После успешной рассылки: Вернуться → ROOT.MENU."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.COME_BACK,
            callback_data=CallbackData.Root.SHOW_MENU,
        )
    )
    return builder.as_markup()


def broadcast_error_ikb() -> InlineKeyboardMarkup:
    """После ошибки рассылки: Попробовать еще раз → шаг 1."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.Common.TRY_AGAIN,
            callback_data=CallbackData.ReleaseNotes.TRY_AGAIN,
        )
    )
    return builder.as_markup()
