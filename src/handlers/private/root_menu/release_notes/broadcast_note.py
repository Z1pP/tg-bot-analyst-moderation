import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.release_note import BroadcastReleaseNoteDTO, GetReleaseNoteByIdDTO
from exceptions import ReleaseNoteNotFoundError
from keyboards.inline.release_notes import (
    confirm_broadcast_release_note_ikb,
    release_note_detail_ikb,
)
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import BroadcastReleaseNoteUseCase, GetReleaseNoteUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(f"{CallbackData.ReleaseNotes.BROADCAST}__"))
async def broadcast_note_start_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик начала рассылки релизной заметки."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    note_id = int(callback.data.split("__")[1])

    dto = GetReleaseNoteByIdDTO(note_id=note_id)
    usecase: GetReleaseNoteUseCase = container.resolve(GetReleaseNoteUseCase)
    try:
        await usecase.execute(dto)
    except ReleaseNoteNotFoundError as e:
        await callback.answer(e.get_user_message(), show_alert=True)
        return

    await state.update_data(broadcast_note_id=note_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.BROADCAST_CONFIRM,
        reply_markup=confirm_broadcast_release_note_ikb(note_id),
    )

    await state.set_state(ReleaseNotesStateManager.broadcasting_note)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_CONFIRM_BROADCAST),
    ReleaseNotesStateManager.broadcasting_note,
)
async def confirm_broadcast_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик подтверждения рассылки."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    parts = callback.data.split("__")
    answer = parts[1]
    note_id = int(parts[2])

    if answer != "yes":
        dto = GetReleaseNoteByIdDTO(note_id=note_id)
        usecase: GetReleaseNoteUseCase = container.resolve(GetReleaseNoteUseCase)
        try:
            result = await usecase.execute(dto)
        except ReleaseNoteNotFoundError as e:
            await callback.answer(e.get_user_message(), show_alert=True)
            return

        text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=result.title,
            content=result.content,
            author=result.author_display_name,
            date=result.date_str,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.ReleaseNotes.BROADCAST_CANCELLED}\n\n{text}",
            reply_markup=release_note_detail_ikb(result.note_id),
        )

        await state.set_state(ReleaseNotesStateManager.view_note)
        return

    try:
        broadcast_dto = BroadcastReleaseNoteDTO(
            note_id=note_id,
            sender_tg_id=str(callback.from_user.id),
        )
        broadcast_usecase: BroadcastReleaseNoteUseCase = container.resolve(
            BroadcastReleaseNoteUseCase
        )
        result = await broadcast_usecase.execute(broadcast_dto)
    except ReleaseNoteNotFoundError:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.NOTE_NOT_FOUND,
        )
        return
    except Exception as e:
        logger.error("Ошибка при рассылке заметки: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.BROADCAST_ERROR,
        )
        return

    if not result.recipients:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.BROADCAST_NO_ADMINS,
        )
        return

    if callback.bot is None:
        return
    success_count = 0
    for recipient in result.recipients:
        try:
            await callback.bot.send_message(
                chat_id=recipient.chat_id,
                text=recipient.text,
            )
            success_count += 1
        except Exception as e:
            logger.error(
                "Ошибка при отправке заметки админу %s: %s",
                recipient.chat_id,
                e,
                exc_info=True,
            )

    d = result.detail_dto
    view_text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
        title=d.title,
        content=d.content,
        author=d.author_display_name,
        date=d.date_str,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"{Dialog.ReleaseNotes.BROADCAST_SUCCESS.format(count=success_count)}\n\n{view_text}",
        reply_markup=release_note_detail_ikb(d.note_id),
    )

    await state.set_state(ReleaseNotesStateManager.view_note)
