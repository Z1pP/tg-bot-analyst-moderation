from aiogram import types


def confirm_action_ikb() -> types.InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(text="Да", callback_data="confirm_action"),
            types.InlineKeyboardButton(text="Нет", callback_data="cancel_action"),
        ],
    ]

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)
