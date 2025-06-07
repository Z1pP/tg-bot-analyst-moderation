from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants import KbCommands
from constants.period import TimePeriod


def get_time_period_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с выбором периода времени для отчетов"""
    periods = TimePeriod.get_all()

    buttons = []
    for i in range(0, len(periods), 2):
        row = periods[i : i + 2]
        buttons.append([KeyboardButton(text=p) for p in row])

    buttons.append([KeyboardButton(text=KbCommands.BACK)])

    # Создаем клавиатуру
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите период отчета",
        selective=True,
    )


def get_time_period_for_full_report() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с выбором периода времени для отчетов"""
    periods = TimePeriod.get_all_periods()

    buttons = []
    for i in range(0, len(periods), 2):
        row = periods[i : i + 2]
        buttons.append([KeyboardButton(text=p) for p in row])

    buttons.append([KeyboardButton(text=KbCommands.MENU)])

    # Создаем клавиатуру
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите период отчета",
        selective=True,
    )
