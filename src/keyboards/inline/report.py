from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import InlineButtons


def _build_order_details_keyboard(
    show_details: bool, back_to_period_callback: str
) -> InlineKeyboardMarkup:
    """Внутренняя функция для создания клавиатуры с детализацией."""
    builder = InlineKeyboardBuilder()

    if show_details:
        builder.row(
            InlineKeyboardButton(
                text="Заказать детализацию",
                callback_data="order_details",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к периоду",
            callback_data=back_to_period_callback,
        )
    )

    return builder.as_markup()


def order_details_kb_single_user(show_details: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура с детализацией для отчета по одному пользователю."""
    return _build_order_details_keyboard(show_details, "back_to_periods")


def order_details_kb_all_users(show_details: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура с детализацией для отчета по всем пользователям."""
    return _build_order_details_keyboard(show_details, "back_to_periods")


def order_details_kb_chat(show_details: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура с детализацией для отчета по чату."""
    return _build_order_details_keyboard(show_details, "back_to_periods")


def hide_details_ikb(message_ids: list[int]) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой скрытия детализации."""
    builder = InlineKeyboardBuilder()
    # Сохраняем ID всех сообщений через запятую
    message_ids_str = ",".join(map(str, message_ids))
    builder.row(
        InlineKeyboardButton(
            text=InlineButtons.MessageButtons.HIDE_DETAILS,
            callback_data=f"hide_details_{message_ids_str}",
        )
    )
    return builder.as_markup()
