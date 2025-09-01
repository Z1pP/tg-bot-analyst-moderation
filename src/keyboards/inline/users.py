from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from dto.user import UserDTO


def users_inline_kb(
    users: List[UserDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопка "Все пользователи"
    builder.row(
        InlineKeyboardButton(
            text="Все пользователи",
            callback_data="all_users",
        )
    )

    # Кнопки пользователей
    start_index = (page - 1) * page_size
    for index, user in enumerate(users):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {user.username}",
                callback_data=f"user__{user.id}",
            )
        )

    # Пагинация (только если больше одной страницы)
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️", callback_data=f"prev_users_page__{page}")
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="users_page_info",
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="▶️", callback_data=f"next_users_page__{page}")
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    return builder.as_markup()


def remove_user_inline_kb(users: list[UserDTO]):
    keyboards = []

    for user in users:
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=f"Удалить {user.username}",
                    callback_data=f"remove_user__{user.id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboards)


def conf_remove_user_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="conf_remove_user__yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="conf_remove_user__no",
        ),
        width=2,
    )
    return builder.as_markup()
