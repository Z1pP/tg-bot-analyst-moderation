"""Archive bind handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import archive_bind_instruction_ikb, chats_menu_ikb
from services.chat import ArchiveBindService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.ARCHIVE_BIND_INSTRUCTION)
async def archive_bind_instruction_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик инструкции по привязке архивного канала."""
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
        archive_bind_service: ArchiveBindService = container.resolve(ArchiveBindService)
        bind_hash = archive_bind_service.generate_bind_hash(
            chat_id=chat_id,
            admin_tg_id=callback.from_user.id,
        )

        instruction_text = Dialog.Chat.ARCHIVE_BIND_WITH_CODE.format(
            instruction=Dialog.Chat.ARCHIVE_BIND_INSTRUCTION,
            bind_hash=bind_hash,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=instruction_text,
            reply_markup=archive_bind_instruction_ikb(),
        )
    except Exception as exc:
        logger.error("Ошибка при генерации hash для привязки: %s", exc)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ARCHIVE_BIND_INSTRUCTION,
            reply_markup=archive_bind_instruction_ikb(),
        )
