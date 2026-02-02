import logging
from typing import Any, Callable

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    cancel_work_hours_setting_ikb,
    chat_actions_ikb,
    time_report_settings_ikb,
)
from models import ChatSession
from services import ChatService
from states import ChatStateManager, WorkHoursState
from usecases.chat import UpdateChatWorkHoursUseCase
from utils.data_parser import parse_breaks_time, parse_time, parse_tolerance
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.REPORT_TIME_SETTING)
async def work_hours_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик открытия меню настройки времени сбора данных"""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if not chat_id:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

        if not chat:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chat_actions_ikb(),
            )
            return

        msg_text = _build_work_hours_view(chat)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=msg_text,
            reply_markup=time_report_settings_ikb(),
        )

        await state.update_data(active_message_id=callback.message.message_id)

    except Exception as e:
        logger.error("Ошибка при открытии меню настройки времени: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=chat_actions_ikb(),
        )


@router.callback_query(F.data == CallbackData.Chat.CHANGE_WORK_START)
async def change_work_start_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения времени начала"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_WORK_START,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(WorkHoursState.waiting_work_start_input)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_WORK_END)
async def change_work_end_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения времени конца"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_WORK_END,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(WorkHoursState.waiting_work_end_input)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_TOLERANCE)
async def change_tolerance_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения отклонения"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_TOLERANCE,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(WorkHoursState.waiting_tolerance_input)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_BREAKS_TIME)
async def change_breaks_time_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения интервала паузы"""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_BREAKS_TIME,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(WorkHoursState.waiting_breaks_time_input)


@router.message(WorkHoursState.waiting_work_start_input)
async def work_start_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода времени начала"""
    await _process_work_hours_input(
        message=message,
        state=state,
        container=container,
        parser=parse_time,
        field_name="start_time",
        error_text="❌ Неверный формат времени!\n\nПожалуйста, пришлите время в формате HH:mm.\n\nНапример: 09:50",
        success_format_func=lambda v: Dialog.Chat.WORK_START_UPDATED.format(
            start_time=v.strftime("%H:%M")
        ),
    )


@router.message(WorkHoursState.waiting_work_end_input)
async def work_end_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода времени конца"""
    await _process_work_hours_input(
        message=message,
        state=state,
        container=container,
        parser=parse_time,
        field_name="end_time",
        error_text="❌ Неверный формат времени!\n\nПожалуйста, пришлите время в формате HH:mm.\n\nНапример: 22:10",
        success_format_func=lambda v: Dialog.Chat.WORK_END_UPDATED.format(
            end_time=v.strftime("%H:%M")
        ),
    )


@router.message(WorkHoursState.waiting_tolerance_input)
async def tolerance_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода отклонения"""
    await _process_work_hours_input(
        message=message,
        state=state,
        container=container,
        parser=parse_tolerance,
        field_name="tolerance",
        error_text="❌ Неверный формат!\n\nПожалуйста, пришлите положительное целое число (минуты).\n\nНапример: 10",
        success_format_func=lambda v: Dialog.Chat.TOLERANCE_UPDATED.format(tolerance=v),
    )


@router.message(WorkHoursState.waiting_breaks_time_input)
async def breaks_time_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода интервала паузы"""
    await _process_work_hours_input(
        message=message,
        state=state,
        container=container,
        parser=parse_breaks_time,
        field_name="breaks_time",
        error_text="❌ Неверный формат!\n\nПожалуйста, пришлите целое число (минуты, можно 0).\n\nНапример: 15",
        success_format_func=lambda v: Dialog.Chat.BREAKS_TIME_UPDATED.format(
            breaks_time=v
        ),
    )


@router.callback_query(F.data == CallbackData.Chat.CANCEL_TIME_SETTING)
async def cancel_work_hours_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик отмены настройки времени"""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if not chat_id:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

        if not chat:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chat_actions_ikb(),
            )
            return

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_ACTIONS_INFO,
            reply_markup=chat_actions_ikb(),
        )

        await state.set_state(ChatStateManager.selecting_chat)

    except Exception as e:
        logger.error("Ошибка при отмене настройки времени: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=chat_actions_ikb(),
        )


async def _process_work_hours_input(
    message: Message,
    state: FSMContext,
    container: Container,
    parser: Callable[[str], Any],
    field_name: str,
    error_text: str,
    success_format_func: Callable[[Any], str],
) -> None:
    """Универсальная функция для обработки ввода настроек времени"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    parsed_value = parser(message.text)

    if parsed_value is None:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=error_text,
                reply_markup=cancel_work_hours_setting_ikb(),
            )
        await message.delete()
        return

    if not chat_id:
        logger.error("chat_id не найден в state")
        await message.delete()
        return

    try:
        usecase: UpdateChatWorkHoursUseCase = container.resolve(
            UpdateChatWorkHoursUseCase
        )

        # Подготавливаем аргументы для execute
        kwargs = {
            "chat_id": chat_id,
            "admin_tg_id": str(message.from_user.id),
            field_name: parsed_value,
        }

        updated_chat = await usecase.execute(**kwargs)

        if not updated_chat:
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text="❌ Чат не найден. Попробуйте позже.",
                    reply_markup=cancel_work_hours_setting_ikb(),
                )
            await message.delete()
            return

        success_message = success_format_func(parsed_value)
        text = Dialog.Chat.WORK_HOURS_UPDATED.format(message=success_message)

        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_work_hours_setting_ikb(),
            )

        await message.delete()

        # Возвращаемся в меню настройки времени
        await _return_to_work_hours_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            container=container,
        )

    except Exception as e:
        logger.error("Ошибка при сохранении %s: %s", field_name, e, exc_info=True)
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text="❌ Произошла ошибка при сохранении. Попробуйте позже.",
                reply_markup=cancel_work_hours_setting_ikb(),
            )
        await message.delete()


async def _return_to_work_hours_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    container: Container,
) -> None:
    """Вспомогательная функция для возврата в меню настройки времени"""
    try:
        db_chat_id = await state.get_value("chat_id")
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=db_chat_id)

        if not chat:
            await safe_edit_message(
                bot=bot,
                chat_id=chat_id,
                message_id=message_id,
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=chat_actions_ikb(),
            )
            return

        msg_text = _build_work_hours_view(chat)

        await safe_edit_message(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            text=msg_text,
            reply_markup=time_report_settings_ikb(),
        )

        await state.set_state(None)
    except Exception as e:
        logger.error(
            "Ошибка при возврате в меню настройки времени: %s", e, exc_info=True
        )


def _build_work_hours_view(chat: ChatSession) -> str:
    """Вспомогательная функция для формирования текста настроек времени"""
    # Проверяем наличие хотя бы одной настройки
    has_any_setting = any(
        [
            chat.start_time is not None,
            chat.end_time is not None,
            chat.tolerance is not None,
            chat.breaks_time is not None,
        ]
    )

    if has_any_setting:
        return Dialog.Chat.TIME_REPORT_EXISTS.format(
            start_time=chat.start_time.strftime("%H:%M")
            if chat.start_time
            else "не указано",
            end_time=chat.end_time.strftime("%H:%M") if chat.end_time else "не указано",
            tolerance=chat.tolerance if chat.tolerance is not None else "не указано",
            breaks_time=chat.breaks_time
            if chat.breaks_time is not None
            else "не указано",
        )
    return Dialog.Chat.TIME_REPORT_NOT_EXISTS
