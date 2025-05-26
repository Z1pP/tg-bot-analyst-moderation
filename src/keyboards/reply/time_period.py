from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from constants.period import TimePeriod


def get_time_period_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с выбором периода времени для отчетов"""
    periods = TimePeriod.get_all()

    buttons = []
    for i in range(0, len(periods), 2):
        row = periods[i : i + 2]
        buttons.append([KeyboardButton(text=p) for p in row])

    # Создаем клавиатуру
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите период отчета",
        selective=True,
    )
