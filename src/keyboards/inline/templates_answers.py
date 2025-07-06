from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import MessageTemplate


def templates_inline_kb(
    templates: List[MessageTemplate],
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
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"remove_template__{template.id}",
            ),
            width=2,
        )

    return builder.as_markup()


def conf_remove_template_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="conf_remove_template__yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="conf_remove_template__no",
        ),
        width=2,
    )
    return builder.as_markup()
