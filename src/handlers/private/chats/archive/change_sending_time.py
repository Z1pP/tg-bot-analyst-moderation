"""Handlers for changing archive report send time."""

import logging
from datetime import time
from typing import Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container
from sqlalchemy.exc import SQLAlchemyError

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import cancel_archive_time_setting_ikb
from services.report_schedule_service import ReportScheduleService
from states import ChatArchiveState
from utils.data_parser import parse_time
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _build_time_prompt() -> str:
    """Build instruction text for time input."""
    return Dialog.Chat.ARCHIVE_TIME_PROMPT


def _build_invalid_time_text() -> str:
    """Build invalid time input error text."""
    return Dialog.Chat.ARCHIVE_TIME_INVALID


def _build_success_text(parsed_time: time) -> str:
    """Build success text with formatted time."""
    return Dialog.Chat.ARCHIVE_TIME_SUCCESS.format(time=parsed_time.strftime("%H:%M"))


async def _safe_delete_message(message: Message) -> None:
    """Delete message ignoring already deleted cases."""
    try:
        await message.delete()
    except TelegramBadRequest:
        logger.debug("Сообщение уже удалено или недоступно для удаления")


@router.callback_query(F.data == CallbackData.Chat.ARCHIVE_TIME_SETTING)
async def change_sending_time_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для изменения/установки времени отправки отчета."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if chat_id is None:
        logger.error("chat_id не найден в state для изменения времени")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ARCHIVE_TIME_CHAT_NOT_FOUND,
            reply_markup=cancel_archive_time_setting_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=_build_time_prompt(),
        reply_markup=cancel_archive_time_setting_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)

    await state.set_state(ChatArchiveState.waiting_time_input)


@router.message(ChatArchiveState.waiting_time_input)
async def time_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик текстового ввода времени отправки."""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    if message.text is None:
        await _safe_delete_message(message)
        return

    parsed_time = parse_time(text=message.text)

    if not parsed_time:
        await _handle_invalid_time(
            message=message,
            active_message_id=active_message_id,
        )
        return

    if chat_id is None:
        logger.error("chat_id не найден в state")
        await _safe_delete_message(message)
        return

    try:
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )

        schedule = await schedule_service.get_schedule(chat_id=chat_id)

        if schedule:
            # Обновляем существующее расписание
            await schedule_service.update_sending_time(
                chat_id=chat_id, new_time=parsed_time
            )
        else:
            # Создаем новое расписание
            await schedule_service.get_or_create_schedule(
                chat_id=chat_id,
                sent_time=parsed_time,
                enabled=True,
            )

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=_build_success_text(parsed_time),
            reply_markup=cancel_archive_time_setting_ikb(),
        )

        await _safe_delete_message(message)
        await state.set_state(None)

    except SQLAlchemyError as exc:
        logger.error("Ошибка при сохранении времени отправки: %s", exc, exc_info=True)
        text = Dialog.Chat.ARCHIVE_TIME_SAVE_ERROR
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_archive_time_setting_ikb(),
            )
        await _safe_delete_message(message)


async def _handle_invalid_time(
    message: Message,
    active_message_id: Optional[int],
) -> None:
    """Notify user about invalid time format."""
    if active_message_id:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=_build_invalid_time_text(),
            reply_markup=cancel_archive_time_setting_ikb(),
        )

    await _safe_delete_message(message)
