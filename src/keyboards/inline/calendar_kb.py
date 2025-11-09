import calendar
from datetime import datetime
from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class CalendarKeyboard:
    """Генератор inline-клавиатуры календаря для выбора диапазона дат."""

    MONTHS_RU = [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ]
    DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    @staticmethod
    def create_calendar(
        year: int,
        month: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> InlineKeyboardMarkup:
        """
        Создает календарь на указанный месяц с выделением выбранного диапазона.

        Args:
            year: Год
            month: Месяц (1-12)
            start_date: Начальная дата диапазона
            end_date: Конечная дата диапазона

        Returns:
            InlineKeyboardMarkup с календарём
        """
        keyboard = []

        # Заголовок с месяцем и годом
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="◀️", callback_data=f"cal_prev_{year}_{month}"
                ),
                InlineKeyboardButton(
                    text=f"{CalendarKeyboard.MONTHS_RU[month - 1]} {year}",
                    callback_data="cal_ignore",
                ),
                InlineKeyboardButton(
                    text="▶️", callback_data=f"cal_next_{year}_{month}"
                ),
            ]
        )

        # Дни недели
        keyboard.append(
            [
                InlineKeyboardButton(text=day, callback_data="cal_ignore")
                for day in CalendarKeyboard.DAYS_RU
            ]
        )

        # Получаем календарь месяца
        month_calendar = calendar.monthcalendar(year, month)

        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    # Пустая ячейка
                    row.append(
                        InlineKeyboardButton(text=" ", callback_data="cal_ignore")
                    )
                else:
                    current_date = datetime(year, month, day)
                    button_text = str(day)

                    # Визуальное выделение выбранных дат
                    if start_date and end_date:
                        if current_date.date() == start_date.date() == end_date.date():
                            button_text = f"◉{day}◉"
                        elif current_date.date() == start_date.date():
                            button_text = f"►{day}"
                        elif current_date.date() == end_date.date():
                            button_text = f"{day}◄"
                        elif start_date.date() < current_date.date() < end_date.date():
                            button_text = f"•{day}•"
                    elif start_date and start_date.date() == current_date.date():
                        button_text = f"◉{day}◉"

                    row.append(
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"cal_day_{year}_{month}_{day}",
                        )
                    )
            keyboard.append(row)

        # Кнопки управления
        control_row = []
        if start_date and end_date:
            control_row.append(
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="cal_confirm")
            )
        if start_date or end_date:
            control_row.append(
                InlineKeyboardButton(text="🔄 Сбросить", callback_data="cal_reset")
            )

        control_row.append(
            InlineKeyboardButton(text="❌ Отмена", callback_data="cal_cancel")
        )

        keyboard.append(control_row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
