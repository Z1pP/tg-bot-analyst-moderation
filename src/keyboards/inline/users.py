from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from dto.user import UserDTO


def users_inline_kb(users: list[UserDTO]):
    keyboards = []

    keyboards.append(
        [
            InlineKeyboardButton(
                text="Все пользователи",
                callback_data="all_users",
            )
        ]
    )

    for index, user in enumerate(users):
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=f"{index + 1}. {user.username}",
                    callback_data=f"user__{user.id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboards)


def remove_user_inline_kb(users: list[UserDTO]):
    keyboards = []

    for index, user in enumerate(users):
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
