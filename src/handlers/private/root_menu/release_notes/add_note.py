import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import RELEASE_NOTES_PAGE_SIZE
from dto.release_note import CreateReleaseNoteDTO, GetReleaseNotesPageDTO
from exceptions import UserNotFoundException
from keyboards.inline.release_notes import (
    cancel_add_release_note_ikb,
    change_title_or_cancel_add_ikb,
    release_notes_menu_ikb,
    select_add_language_ikb,
)
from states.release_notes import ReleaseNotesStateManager
from usecases.release_notes import CreateReleaseNoteUseCase, GetReleaseNotesPageUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.ReleaseNotes.ADD)
async def add_note_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала добавления релизной заметки"""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
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

    await state.set_state(ReleaseNotesStateManager.selecting_add_language)


@router.message(ReleaseNotesStateManager.waiting_for_title)
async def add_note_title_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода заголовка релизной заметки"""
    if message.text is None:
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
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=content_input_text,
            reply_markup=change_title_or_cancel_add_ikb(),
        )
    else:
        sent_msg = await message.answer(
            content_input_text,
            reply_markup=change_title_or_cancel_add_ikb(),
        )
        await state.update_data(active_message_id=sent_msg.message_id)

    await state.set_state(ReleaseNotesStateManager.waiting_for_content)


@router.message(ReleaseNotesStateManager.waiting_for_content)
async def add_note_content_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода содержимого релизной заметки и сохранение"""
    if message.text is None or message.from_user is None:
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

    note_language = data.get("note_language")
    if not note_language:
        await message.reply(
            "Ошибка: язык заметки не найден. Пожалуйста, начните заново."
        )
        await state.clear()
        return

    create_dto = CreateReleaseNoteDTO(
        title=title,
        content=content,
        language=note_language,
        author_tg_id=str(message.from_user.id),
    )
    create_usecase: CreateReleaseNoteUseCase = container.resolve(
        CreateReleaseNoteUseCase
    )

    try:
        await create_usecase.execute(create_dto)
    except UserNotFoundException as e:
        await message.reply(e.get_user_message())
        await state.clear()
        return

    # Возвращаемся к списку заметок
    page_dto = GetReleaseNotesPageDTO(
        language=note_language, page=1, page_size=RELEASE_NOTES_PAGE_SIZE
    )
    page_usecase: GetReleaseNotesPageUseCase = container.resolve(
        GetReleaseNotesPageUseCase
    )
    page_result = await page_usecase.execute(page_dto)

    text = (
        Dialog.ReleaseNotes.NO_RELEASE_NOTES
        if not page_result.notes
        else Dialog.ReleaseNotes.RELEASE_NOTES_MENU
    )
    final_text = f"{Dialog.ReleaseNotes.NOTE_ADDED}\n\n{text}"
    final_markup = release_notes_menu_ikb(
        page_result.notes, page_result.page, page_result.total_pages
    )

    if active_message_id:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=final_text,
            reply_markup=final_markup,
        )
    else:
        # Если active_message_id не найден, отправляем новое сообщение
        await message.answer(
            final_text,
            reply_markup=final_markup,
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
async def cancel_add_note_handler(
    callback: CallbackQuery, state: FSMContext, container: Container, user_language: str
) -> None:
    """Обработчик отмены добавления релизной заметки"""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return

    page_dto = GetReleaseNotesPageDTO(
        language=user_language, page=1, page_size=RELEASE_NOTES_PAGE_SIZE
    )
    usecase: GetReleaseNotesPageUseCase = container.resolve(GetReleaseNotesPageUseCase)
    result = await usecase.execute(page_dto)

    text = (
        Dialog.ReleaseNotes.NO_RELEASE_NOTES
        if not result.notes
        else Dialog.ReleaseNotes.RELEASE_NOTES_MENU
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=release_notes_menu_ikb(
            result.notes, result.page, result.total_pages
        ),
    )

    await state.set_state(ReleaseNotesStateManager.menu)


@router.callback_query(
    F.data.startswith(CallbackData.ReleaseNotes.PREFIX_SELECT_ADD_LANGUAGE),
    ReleaseNotesStateManager.selecting_add_language,
)
async def select_add_language_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора языка для новой заметки"""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, Message):
        return

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

    await state.set_state(ReleaseNotesStateManager.waiting_for_title)


@router.callback_query(
    F.data == CallbackData.ReleaseNotes.CHANGE_TITLE_WHILE_ADDING,
    ReleaseNotesStateManager.waiting_for_content,
)
async def change_title_while_adding_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик изменения заголовка при добавлении релизной заметки"""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, Message):
        return

    await state.update_data(active_message_id=callback.message.message_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.ReleaseNotes.TITLE_INPUT,
        reply_markup=cancel_add_release_note_ikb(),
    )

    await state.set_state(ReleaseNotesStateManager.waiting_for_title)
