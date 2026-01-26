"""Archive schedule toggle handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import archive_channel_setting_ikb, chats_menu_ikb
from services import ChatService
from services.messaging import BotMessageService
from services.report_schedule_service import ReportScheduleService
from utils.archive import build_schedule_info
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
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )
        chat_service: ChatService = container.resolve(ChatService)

        schedule = await schedule_service.get_schedule(chat_id=chat_id)

        if not schedule:
            await callback.answer(
                "❌ Расписание не найдено. Сначала настройте время отправки.",
                show_alert=True,
            )
            return

        new_enabled = not schedule.enabled
        updated_schedule = await schedule_service.toggle_schedule(
            chat_id=chat_id, enabled=new_enabled
        )

        if not updated_schedule:
            await callback.answer(
                "❌ Ошибка при обновлении расписания", show_alert=True
            )
            return

        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
        if not chat or not chat.archive_chat:
            await callback.answer("❌ Чат не найден", show_alert=True)
            return

        schedule_info, schedule_enabled = build_schedule_info(updated_schedule)
        text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(
            title=chat.title, schedule_info=schedule_info
        )

        bot_message_service: BotMessageService = container.resolve(BotMessageService)
        invite_link = await bot_message_service.get_chat_invite_link(
            chat_tgid=chat.archive_chat.chat_id
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=archive_channel_setting_ikb(
                archive_chat=chat.archive_chat or None,
                invite_link=invite_link,
                schedule_enabled=schedule_enabled,
            ),
        )
    except Exception as exc:
        logger.error("Ошибка при переключении рассылки: %s", exc, exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)
