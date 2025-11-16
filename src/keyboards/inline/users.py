from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.pagination import USERS_PAGE_SIZE
from dto.user import UserDTO


def users_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура меню пользователей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.SELECT_USER,
            callback_data="select_user",
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.ADD_USER,
            callback_data="add_user",
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.REMOVE_USER,
            callback_data="remove_user",
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_MAIN_MENU,
            callback_data="back_to_main_menu_from_users",
        )
    )

    return builder.as_markup()


def cancel_add_user_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для отмены добавления пользователя"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.CANCEL,
            callback_data="cancel_add_user",
        )
    )
    return builder.as_markup()


def users_inline_kb(
    users: List[UserDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = USERS_PAGE_SIZE,
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

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data="users_menu",
        )
    )

    return builder.as_markup()


def remove_user_inline_kb(
    users: List[UserDTO],
    page: int = 1,
    total_count: int = 0,
    page_size: int = USERS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки удаления пользователей
    start_index = (page - 1) * page_size
    for index, user in enumerate(users):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. Удалить {user.username}",
                callback_data=f"remove_user__{user.id}",
            )
        )

    # Пагинация (только если больше одной страницы)
    if total_count > page_size:
        max_pages = (total_count + page_size - 1) // page_size
        pagination_buttons = []

        # Кнопка "Назад"
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️", callback_data=f"prev_remove_users_page__{page}"
                )
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data="remove_users_page_info",
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️", callback_data=f"next_remove_users_page__{page}"
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data="users_menu",
        )
    )

    return builder.as_markup()


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
