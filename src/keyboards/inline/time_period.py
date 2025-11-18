from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import KbCommands
from constants.callback import CallbackData
from constants.period import TimePeriod


def _build_time_period_keyboard(
    include_custom: bool, back_callback: str
) -> InlineKeyboardMarkup:
    """Внутренняя функция для создания клавиатуры с выбором периода."""
    builder = InlineKeyboardBuilder()

    periods = TimePeriod.get_all() if include_custom else TimePeriod.get_all_periods()

    # Добавляем кнопки периодов по 2 в ряд
    for i in range(0, len(periods), 2):
        row_periods = periods[i : i + 2]
        buttons = [
            InlineKeyboardButton(
                text=period,
                callback_data=f"{CallbackData.Report.PREFIX_PERIOD}{period}",
            )
            for period in row_periods
        ]
        builder.row(*buttons)

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text=KbCommands.BACK,
            callback_data=back_callback,
        )
    )

    return builder.as_markup()


def time_period_ikb_single_user(include_custom: bool = True) -> InlineKeyboardMarkup:
    """Создает inline клавиатуру с выбором периода времени для отчетов по одному пользователю."""
    return _build_time_period_keyboard(
        include_custom, CallbackData.Report.BACK_TO_SINGLE_USER_ACTIONS
    )


def time_period_ikb_all_users(include_custom: bool = True) -> InlineKeyboardMarkup:
    """Создает inline клавиатуру с выбором периода времени для отчетов по всем пользователям."""
    return _build_time_period_keyboard(
        include_custom, CallbackData.Report.BACK_TO_ALL_USERS_ACTIONS
    )


def time_period_ikb_chat(include_custom: bool = True) -> InlineKeyboardMarkup:
    """Создает inline клавиатуру с выбором периода времени для отчетов по чату."""
    return _build_time_period_keyboard(
        include_custom, CallbackData.Chat.BACK_TO_CHAT_ACTIONS
    )
