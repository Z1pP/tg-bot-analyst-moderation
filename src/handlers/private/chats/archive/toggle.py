"""Archive schedule toggle handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from keyboards.inline.chats import chats_menu_ikb
from usecases.archive import ToggleArchiveScheduleUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.ARCHIVE_TOGGLE_SCHEDULE)
async def archive_toggle_schedule_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик переключения рассылки."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")

    if chat_id is None:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    try:
        usecase: ToggleArchiveScheduleUseCase = container.resolve(
            ToggleArchiveScheduleUseCase
        )
        result = await usecase.execute(chat_id=chat_id)

        if result is None:
            await callback.answer(
                "❌ Расписание не найдено. Сначала настройте время отправки.",
                show_alert=True,
            )
            return

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=result.text,
            reply_markup=result.reply_markup,
        )
    except BotBaseException as e:
        await callback.answer(e.get_user_message(), show_alert=True)
    except Exception as exc:
        raise_business_logic(
            "Ошибка при переключении рассылки.",
            "❌ Произошла ошибка при переключении рассылки.",
            exc,
            logger,
        )
