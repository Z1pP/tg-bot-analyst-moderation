from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import QuickResponse


def templates_inline_kb(
    templates: List[QuickResponse],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if not templates:
        builder.row(
            InlineKeyboardButton(
                text="Шаблонов не найдено, создайте шаблон",
                callback_data="templates_not_found",
            )
        )
        return builder.as_markup()

    for index, template in enumerate(templates):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {template.title}",
                callback_data=f"template__{template.id}",
            )
        )

    return builder.as_markup()
