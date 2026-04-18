"""Колбэк «Отменить» на карточке авто-модерации."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.callback import CallbackData
from constants.enums import ChatType

from .staff import is_automoderation_staff

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(
    F.data == CallbackData.AutoModeration.CANCEL,
    F.message.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
)
async def automoderation_cancel_handler(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    """Отменяет действие и удаляет карточку без действий (только staff)."""
    if not await is_automoderation_staff(callback, container):
        await callback.answer(
            "\u26d4 Недостаточно прав для этого действия.",
            show_alert=True,
        )
        return

    await callback.answer("Действие отменено")
    await state.clear()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning("automod cancel: не удалось удалить сообщение: %s", e)
