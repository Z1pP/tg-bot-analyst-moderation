from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons
from constants.callback import CallbackData
from constants.enums import UserRole
from constants.pagination import USERS_PAGE_SIZE
from dto.user import UserDTO


def users_menu_ikb() -> InlineKeyboardMarkup:
    """Клавиатура меню пользователей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.SELECT_USER,
            callback_data=CallbackData.User.SELECT_USER,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.ADD_USER,
            callback_data=CallbackData.User.ADD,
        ),
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.REMOVE_USER,
            callback_data=CallbackData.User.REMOVE,
        ),
        width=2,
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_MAIN_MENU,
            callback_data=CallbackData.User.BACK_TO_MAIN_MENU_FROM_USERS,
        )
    )

    return builder.as_markup()


def cancel_add_user_ikb() -> InlineKeyboardMarkup:
    """Клавиатура для отмены добавления пользователя"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.CANCEL,
            callback_data=CallbackData.User.CANCEL_ADD,
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
            callback_data=CallbackData.User.ALL_USERS,
        )
    )

    # Кнопки пользователей
    start_index = (page - 1) * page_size
    for index, user in enumerate(users):
        builder.row(
            InlineKeyboardButton(
                text=f"{start_index + index + 1}. {user.username}",
                callback_data=f"{CallbackData.User.PREFIX_USER}{user.id}",
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
                    text="◀️",
                    callback_data=f"{CallbackData.User.PREFIX_PREV_USERS_PAGE}{page}",
                )
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data=CallbackData.User.USERS_PAGE_INFO,
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"{CallbackData.User.PREFIX_NEXT_USERS_PAGE}{page}",
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.USERS_MENU,
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
                callback_data=f"{CallbackData.User.PREFIX_REMOVE_USER}{user.id}",
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
                    text="◀️",
                    callback_data=f"{CallbackData.User.PREFIX_PREV_REMOVE_USERS_PAGE}{page}",
                )
            )

        # Информация о странице
        start_item = (page - 1) * page_size + 1
        end_item = min(page * page_size, total_count)
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{start_item}-{end_item} из {total_count}",
                callback_data=CallbackData.User.REMOVE_USERS_PAGE_INFO,
            )
        )

        # Кнопка "Вперед"
        if page < max_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"{CallbackData.User.PREFIX_NEXT_REMOVE_USERS_PAGE}{page}",
                )
            )

        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Кнопка возврата в меню (в самом низу)
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.USERS_MENU,
        )
    )

    return builder.as_markup()


def conf_remove_user_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data=f"{CallbackData.User.PREFIX_CONFIRM_REMOVE_USER}yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data=f"{CallbackData.User.PREFIX_CONFIRM_REMOVE_USER}no",
        ),
        width=2,
    )
    return builder.as_markup()


def user_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий с выбранным пользователем"""
    from constants import Dialog

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Report.GET_REPORT,
            callback_data=CallbackData.Report.GET_USER_REPORT,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=Dialog.User.SELECT_USER,
            callback_data=CallbackData.User.SELECT_USER,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.USERS_MENU,
        )
    )

    return builder.as_markup()


def all_users_actions_ikb() -> InlineKeyboardMarkup:
    """Клавиатура действий со всеми пользователями"""
    from constants import Dialog

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=Dialog.Report.GET_REPORT,
            callback_data=CallbackData.Report.GET_ALL_USERS_REPORT,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=Dialog.User.SELECT_USER,
            callback_data=CallbackData.User.SELECT_USER,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.UserButtons.BACK_TO_USERS_MENU,
            callback_data=CallbackData.User.USERS_MENU,
        )
    )

    return builder.as_markup()


def role_select_ikb(user_id: int, current_role: UserRole) -> InlineKeyboardMarkup:
    """Клавиатура для выбора роли пользователя"""
    builder = InlineKeyboardBuilder()

    # Определяем текст для каждой роли с отметкой текущей роли
    admin_text = "👑 Администратор"
    moderator_text = "🛡️ Модератор"
    user_text = "👤 Пользователь"

    if current_role == UserRole.ADMIN:
        admin_text = "✅ " + admin_text
    elif current_role == UserRole.MODERATOR:
        moderator_text = "✅ " + moderator_text
    elif current_role == UserRole.USER:
        user_text = "✅ " + user_text

    # Кнопки для выбора роли
    builder.row(
        InlineKeyboardButton(
            text=admin_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=moderator_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__moderator",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=user_text,
            callback_data=f"{CallbackData.User.PREFIX_ROLE_SELECT}{user_id}__user",
        )
    )

    return builder.as_markup()
