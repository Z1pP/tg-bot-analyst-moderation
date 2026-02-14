"""Сценарий рассылки релизной заметки: ввод текста → выбор языка → подтверждение → рассылка."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.release_note import BroadcastTextDTO
from keyboards.inline.release_notes import (
    broadcast_confirm_ikb,
    broadcast_error_ikb,
    broadcast_step1_ikb,
    broadcast_step2_ikb,
    broadcast_success_ikb,
)
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import BroadcastTextToAdminsUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.SHOW_MENU)
async def release_notes_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Вход: просьба ввести текст заметки и кнопка «Вернуться»."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.INPUT_NOTE_TEXT,
        reply_markup=broadcast_step1_ikb(),
    )
    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(ReleaseNotesStateManager.waiting_for_note_text)


@router.message(ReleaseNotesStateManager.waiting_for_note_text, F.text)
async def broadcast_note_text_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """После ввода текста: сохранить в FSM, показать выбор языка (RU/EN)."""
    if message.text is None:
        return
    text = message.text.strip()
    if not text:
        return
    await state.update_data(broadcast_note_text=text)
    await state.set_state(ReleaseNotesStateManager.selecting_broadcast_language)

    try:
        await message.delete()
    except Exception:
        logger.warning(
            "Не удалось удалить сообщение пользователя: %s", message.message_id
        )

    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    if active_message_id is not None:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.ReleaseNotes.SELECT_BROADCAST_LANGUAGE,
            reply_markup=broadcast_step2_ikb(),
        )
    else:
        await message.answer(
            Dialog.ReleaseNotes.SELECT_BROADCAST_LANGUAGE,
            reply_markup=broadcast_step2_ikb(),
        )


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CHANGE_NOTE_TEXT,
    ReleaseNotesStateManager.selecting_broadcast_language,
)
async def broadcast_change_text_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """«Изменить текст заметки»: вернуть на шаг 1."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await state.set_state(ReleaseNotesStateManager.waiting_for_note_text)
    await state.update_data(broadcast_note_text=None)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.INPUT_NOTE_TEXT,
        reply_markup=broadcast_step1_ikb(),
    )


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_BROADCAST_LANG),
    ReleaseNotesStateManager.selecting_broadcast_language,
)
async def broadcast_select_language_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Выбор RU/EN: сохранить язык, показать превью и Да/Нет."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

    lang_code = callback.data.replace(
        CallbackData.ReleaseNotes.PREFIX_BROADCAST_LANG, ""
    )
    data = await state.get_data()
    text = data.get("broadcast_note_text") or ""
    await state.update_data(broadcast_language=lang_code)
    await state.set_state(ReleaseNotesStateManager.confirming_broadcast)

    language_label = "RU" if lang_code.lower() == "ru" else "EN"
    preview_text = Dialog.ReleaseNotes.BROADCAST_CONFIRM_PREVIEW.format(
        text=text,
        language=language_label,
    )
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=preview_text,
        reply_markup=broadcast_confirm_ikb(),
    )


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CONFIRM_BROADCAST_YES,
    ReleaseNotesStateManager.confirming_broadcast,
)
async def broadcast_confirm_yes_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Подтверждение «Да»: рассылка получателям; при успехе/ошибке — соответствующее сообщение."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    if callback.bot is None:
        return

    data = await state.get_data()
    text = data.get("broadcast_note_text") or ""
    language = data.get("broadcast_language") or "ru"

    usecase: BroadcastTextToAdminsUseCase = container.resolve(
        BroadcastTextToAdminsUseCase
    )
    dto = BroadcastTextDTO(text=text, language=language)
    try:
        recipients = await usecase.execute(dto)
    except Exception as e:
        logger.error("Ошибка при подготовке рассылки: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.BROADCAST_ERROR_RETRY,
            reply_markup=broadcast_error_ikb(),
        )
        return

    success_count = 0
    for recipient in recipients:
        try:
            await callback.bot.send_message(
                chat_id=recipient.chat_id,
                text=recipient.text,
            )
            success_count += 1
        except Exception as e:
            logger.error(
                "Ошибка при отправке заметки получателю %s: %s",
                recipient.chat_id,
                e,
                exc_info=True,
            )

    if success_count < len(recipients) or (recipients and success_count == 0):
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.BROADCAST_ERROR_RETRY,
            reply_markup=broadcast_error_ikb(),
        )
        return

    success_msg = (
        Dialog.ReleaseNotes.BROADCAST_SUCCESS_RU
        if language.lower() == "ru"
        else Dialog.ReleaseNotes.BROADCAST_SUCCESS_EN
    )
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=success_msg,
        reply_markup=broadcast_success_ikb(),
    )
    await state.clear()


@router.callback_query(F.data == CallbackData.ReleaseNotes.TRY_AGAIN)
async def broadcast_try_again_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """«Попробовать еще раз» после ошибки: вернуть на шаг 1."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await state.clear()
    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(ReleaseNotesStateManager.waiting_for_note_text)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.INPUT_NOTE_TEXT,
        reply_markup=broadcast_step1_ikb(),
    )
