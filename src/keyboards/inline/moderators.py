from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from dto.user import UserDTO


def moderators_inline_kb(users: list[UserDTO]):
    keyboards = []

    for index, user in enumerate(users):
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=f"{index + 1}. {user.username}",
                    callback_data=f"user__{user.username}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboards)
