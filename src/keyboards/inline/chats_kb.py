from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from dto.chat_dto import ChatReadDTO


def chats_inline_kb(chats: list[ChatReadDTO]) -> InlineKeyboardMarkup:
    keyboards = []

    keyboards.append(
        [
            InlineKeyboardButton(
                text="Все чаты",
                callback_data="all_chats",
            )
        ]
    )

    for index, chat in enumerate(chats):
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=f"{index + 1}. {chat.title}",
                    callback_data=f"chat__{chat.title}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboards)
