import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from keyboards.inline.release_notes import (
    confirm_broadcast_release_note_ikb,
    release_note_detail_ikb,
)
from repositories import UserRepository
from services.release_note_service import ReleaseNoteService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(f"{CallbackData.ReleaseNotes.BROADCAST}__"))
async def broadcast_note_start_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик начала рассылки релизной заметки"""
    await callback.answer()

    note_id = int(callback.data.split("__")[1])

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    note = await release_note_service.get_note_by_id(note_id)

    if not note:
        await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
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
    """Обработчик подтверждения рассылки"""
    await callback.answer()

    parts = callback.data.split("__")
    answer = parts[1]
    note_id = int(parts[2])

    if answer != "yes":
        # Возвращаемся к просмотру заметки
        release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
        note = await release_note_service.get_note_by_id(note_id)

        if not note:
            await callback.answer(Dialog.ReleaseNotes.NOTE_NOT_FOUND, show_alert=True)
            return

        # Получаем автора
        author_name = "Unknown"
        if note.author:
            author_name = note.author.username or str(note.author.tg_id)

        text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=note.title,
            content=note.content,
            author=author_name,
            date=note.created_at.strftime("%d.%m.%Y %H:%M"),
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.ReleaseNotes.BROADCAST_CANCELLED}\n\n{text}",
            reply_markup=release_note_detail_ikb(note_id),
        )

        await state.set_state(ReleaseNotesStateManager.view_note)
        return

    try:
        release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
        note = await release_note_service.get_note_by_id(note_id)

        if not note:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.ReleaseNotes.NOTE_NOT_FOUND,
            )
            return

        # Получаем язык заметки и нормализуем его
        note_language = (
            note.language.split("-")[0].lower() if note.language else DEFAULT_LANGUAGE
        )

        # Получаем список всех админов
        user_repository: UserRepository = container.resolve(UserRepository)
        admins = await user_repository.get_all_admins()

        # Фильтруем админов: исключаем текущего пользователя и фильтруем по языку
        admins_to_send = []
        for admin in admins:
            if admin.tg_id != user_tg_id and admin.tg_id:
                # Получаем язык админа и нормализуем его
                admin_language = (
                    admin.language.split("-")[0].lower()
                    if admin.language
                    else DEFAULT_LANGUAGE
                )
                # Отправляем только если язык админа совпадает с языком заметки
                if admin_language == note_language:
                    admins_to_send.append(admin)

        if not admins_to_send:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.ReleaseNotes.BROADCAST_NO_ADMINS,
            )
            return

        # Формируем текст сообщения
        author_name = "Unknown"
        if note.author:
            author_name = note.author.username or str(note.author.tg_id)

        broadcast_text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=note.title,
            content=note.content,
            author=author_name,
            date=note.created_at.strftime("%d.%m.%Y %H:%M"),
        )

        # Отправляем сообщения админам
        success_count = 0
        for admin in admins_to_send:
            try:
                await callback.bot.send_message(
                    chat_id=int(admin.tg_id),
                    text=broadcast_text,
                )
                success_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке заметки админу {admin.tg_id}: {e}",
                    exc_info=True,
                )

        # Возвращаемся к просмотру заметки
        text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=note.title,
            content=note.content,
            author=author_name,
            date=note.created_at.strftime("%d.%m.%Y %H:%M"),
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.ReleaseNotes.BROADCAST_SUCCESS.format(count=success_count)}\n\n{text}",
            reply_markup=release_note_detail_ikb(note_id),
        )

        await state.set_state(ReleaseNotesStateManager.view_note)

    except Exception as e:
        logger.error("Ошибка при рассылке заметки: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.ReleaseNotes.BROADCAST_ERROR,
        )
