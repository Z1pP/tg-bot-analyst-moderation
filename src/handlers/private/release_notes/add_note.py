import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.release_notes import (
    cancel_add_release_note_ikb,
    change_title_or_cancel_add_ikb,
    release_notes_menu_ikb,
    select_add_language_ikb,
)
from services.release_note_service import ReleaseNoteService
from services.user import UserService
from states.release_notes import ReleaseNotesStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name="add_release_note_router")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.ADD)
async def add_note_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала добавления релизной заметки"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()

    # Проверка прав доступа
    user_tg_id = str(callback.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await callback.answer("У вас нет прав для добавления заметок", show_alert=True)
        return

    # Показываем выбор языка для новой заметки
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.SELECT_ADD_LANGUAGE,
        reply_markup=select_add_language_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.selecting_add_language,
    )


@router.message(ReleaseNotesStateManager.waiting_for_title)
async def add_note_title_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода заголовка релизной заметки"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    # Проверка прав доступа
    user_tg_id = str(message.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await message.reply("У вас нет прав для добавления заметок")
        await state.clear()
        return

    title = message.text
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    await state.update_data(title=title)

    # Удаляем сообщение пользователя с заголовком
    try:
        await message.delete()
    except Exception:
        logger.warning(
            f"Не удалось удалить сообщение пользователя: {message.message_id}"
        )

    # Редактируем предыдущее сообщение или отправляем новое с кнопками
    content_input_text = Dialog.ReleaseNotes.CONTENT_INPUT.format(title=title)
    if active_message_id:
        try:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=content_input_text,
                reply_markup=change_title_or_cancel_add_ikb(),
            )
        except Exception:
            # Если не удалось отредактировать, отправляем новое сообщение
            sent_msg = await message.answer(
                content_input_text,
                reply_markup=change_title_or_cancel_add_ikb(),
            )
            await state.update_data(active_message_id=sent_msg.message_id)
    else:
        sent_msg = await message.answer(
            content_input_text,
            reply_markup=change_title_or_cancel_add_ikb(),
        )
        await state.update_data(active_message_id=sent_msg.message_id)

    await state.set_state(ReleaseNotesStateManager.waiting_for_content)


@router.message(ReleaseNotesStateManager.waiting_for_content)
async def add_note_content_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода содержимого релизной заметки и сохранение"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    # Проверка прав доступа
    user_tg_id = str(message.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await message.reply("У вас нет прав для добавления заметок")
        await state.clear()
        return

    content = message.text
    data = await state.get_data()
    title = data.get("title")
    active_message_id = data.get("active_message_id")

    # Проверяем наличие заголовка
    if not title:
        await message.reply("Ошибка: заголовок не найден. Пожалуйста, начните заново.")
        await state.clear()
        return

    # Удаляем сообщение пользователя с содержимым
    try:
        await message.delete()
    except Exception:
        logger.warning(
            f"Не удалось удалить сообщение пользователя: {message.message_id}"
        )

    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(message.from_user.id))
    author_id = db_user.id

    # Получаем язык заметки из state
    note_language = data.get("note_language")
    if not note_language:
        await message.reply(
            "Ошибка: язык заметки не найден. Пожалуйста, начните заново."
        )
        await state.clear()
        return

    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)
    await release_note_service.create_note(
        title=title, content=content, language=note_language, author_id=author_id
    )

    # Возвращаемся к списку заметок
    page = 1
    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(note_language, limit, offset)
    total_count = await release_note_service.count_notes(note_language)
    total_pages = math.ceil(total_count / limit)

    if not notes:
        text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
    else:
        text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

    # Используем active_message_id для редактирования сообщения бота
    if active_message_id:
        try:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"{Dialog.ReleaseNotes.NOTE_ADDED}\n\n{text}",
                reply_markup=release_notes_menu_ikb(
                    notes, page, total_pages, user_tg_id=str(message.from_user.id)
                ),
            )
        except Exception:
            # Если не удалось отредактировать, отправляем новое сообщение
            await message.answer(
                f"{Dialog.ReleaseNotes.NOTE_ADDED}\n\n{text}",
                reply_markup=release_notes_menu_ikb(
                    notes, page, total_pages, user_tg_id=str(message.from_user.id)
                ),
            )
    else:
        # Если active_message_id не найден, отправляем новое сообщение
        await message.answer(
            f"{Dialog.ReleaseNotes.NOTE_ADDED}\n\n{text}",
            reply_markup=release_notes_menu_ikb(
                notes, page, total_pages, user_tg_id=str(message.from_user.id)
            ),
        )

    await state.clear()


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_ADD,
    ReleaseNotesStateManager.selecting_add_language,
)
@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_ADD,
    ReleaseNotesStateManager.waiting_for_title,
)
@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CANCEL_ADD,
    ReleaseNotesStateManager.waiting_for_content,
)
async def cancel_add_note_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены добавления релизной заметки"""
    await callback.answer()

    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    # Возвращаемся к списку заметок
    release_note_service: ReleaseNoteService = container.resolve(ReleaseNoteService)

    page = 1
    limit = 10
    offset = (page - 1) * limit

    notes = await release_note_service.get_notes(user_language, limit, offset)
    total_count = await release_note_service.count_notes(user_language)
    total_pages = math.ceil(total_count / limit)

    if not notes:
        text = Dialog.ReleaseNotes.NO_RELEASE_NOTES
    else:
        text = Dialog.ReleaseNotes.RELEASE_NOTES_MENU

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(
            notes, page, total_pages, user_tg_id=str(callback.from_user.id)
        ),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.menu,
    )


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT_ADD_LANGUAGE),
    ReleaseNotesStateManager.selecting_add_language,
)
async def select_add_language_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора языка для новой заметки"""
    from constants import RELEASE_NOTES_ADMIN_IDS

    await callback.answer()

    # Проверка прав доступа
    user_tg_id = str(callback.from_user.id)
    if user_tg_id not in RELEASE_NOTES_ADMIN_IDS:
        await callback.answer("У вас нет прав для добавления заметок", show_alert=True)
        await state.clear()
        return

    # Извлекаем язык из callback_data
    lang_code = callback.data.split(
        CallbackData.ReleaseNotes.PREFIX_SELECT_ADD_LANGUAGE
    )[1]

    await state.update_data(
        active_message_id=callback.message.message_id,
        note_language=lang_code,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.TITLE_INPUT,
        reply_markup=cancel_add_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.waiting_for_title,
    )


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CHANGE_TITLE_WHILE_ADDING,
    ReleaseNotesStateManager.waiting_for_content,
)
async def change_title_while_adding_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик изменения заголовка при добавлении релизной заметки"""
    await callback.answer()

    await state.update_data(active_message_id=callback.message.message_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.TITLE_INPUT,
        reply_markup=cancel_add_release_note_ikb(),
    )

    await log_and_set_state(
        callback.message,
        state,
        ReleaseNotesStateManager.waiting_for_title,
    )
