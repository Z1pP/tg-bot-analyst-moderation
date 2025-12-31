import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import (
    cancel_work_hours_setting_ikb,
    chat_actions_ikb,
    work_hours_menu_ikb,
)
from services import ChatService
from states import ChatStateManager, WorkHoursState
from usecases.chat import UpdateChatWorkHoursUseCase
from utils.data_parser import parse_time, parse_tolerance
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.REPORT_TIME_SETTING)
async def work_hours_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
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

        msg = await callback.message.edit_text(
            text=Dialog.Chat.WORK_HOURS_MENU.format(
                start_time=chat.start_time.strftime("%H:%M"),
                end_time=chat.end_time.strftime("%H:%M"),
                tolerance=chat.tolerance,
            ),
            reply_markup=work_hours_menu_ikb(),
        )

        await state.update_data(active_message_id=msg.message_id)

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

    msg = await callback.message.edit_text(
        text=Dialog.Chat.ENTER_WORK_START,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=msg.message_id)
    await state.set_state(WorkHoursState.waiting_work_start_input)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_WORK_END)
async def change_work_end_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения времени конца"""
    await callback.answer()

    msg = await callback.message.edit_text(
        text=Dialog.Chat.ENTER_WORK_END,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=msg.message_id)
    await state.set_state(WorkHoursState.waiting_work_end_input)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_TOLERANCE)
async def change_tolerance_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора изменения отклонения"""
    await callback.answer()

    msg = await callback.message.edit_text(
        text=Dialog.Chat.ENTER_TOLERANCE,
        reply_markup=cancel_work_hours_setting_ikb(),
    )

    await state.update_data(active_message_id=msg.message_id)
    await state.set_state(WorkHoursState.waiting_tolerance_input)


@router.message(WorkHoursState.waiting_work_start_input)
async def work_start_input_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода времени начала"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    parsed_time = parse_time(text=message.text)

    if not parsed_time:
        if active_message_id:
            text = (
                "❌ Неверный формат времени!\n\n"
                "Пожалуйста, пришлите время в формате HH:mm.\n\n"
                "Например: 09:50"
            )
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
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
        updated_chat = await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(message.from_user.id),
            start_time=parsed_time,
        )

        if not updated_chat:
            text = "❌ Чат не найден. Попробуйте позже."
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=cancel_work_hours_setting_ikb(),
                )
            await message.delete()
            return

        success_message = Dialog.Chat.WORK_START_UPDATED.format(
            start_time=parsed_time.strftime("%H:%M")
        )
        text = Dialog.Chat.WORK_HOURS_UPDATED.format(message=success_message)

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=cancel_work_hours_setting_ikb(),
        )

        await message.delete()

        # Возвращаемся в меню действий чата
        await _return_to_chat_actions(
            message.bot, message.chat.id, active_message_id, updated_chat, state
        )

    except Exception as e:
        logger.error("Ошибка при сохранении времени начала: %s", e, exc_info=True)
        text = "❌ Произошла ошибка при сохранении времени. Попробуйте позже."
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_work_hours_setting_ikb(),
            )
        await message.delete()


@router.message(WorkHoursState.waiting_work_end_input)
async def work_end_input_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода времени конца"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    parsed_time = parse_time(text=message.text)

    if not parsed_time:
        if active_message_id:
            text = (
                "❌ Неверный формат времени!\n\n"
                "Пожалуйста, пришлите время в формате HH:mm.\n\n"
                "Например: 22:10"
            )
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
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
        updated_chat = await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(message.from_user.id),
            end_time=parsed_time,
        )

        if not updated_chat:
            text = "❌ Чат не найден. Попробуйте позже."
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=cancel_work_hours_setting_ikb(),
                )
            await message.delete()
            return

        success_message = Dialog.Chat.WORK_END_UPDATED.format(
            end_time=parsed_time.strftime("%H:%M")
        )
        text = Dialog.Chat.WORK_HOURS_UPDATED.format(message=success_message)

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=cancel_work_hours_setting_ikb(),
        )

        await message.delete()

        # Возвращаемся в меню действий чата
        await _return_to_chat_actions(
            message.bot, message.chat.id, active_message_id, updated_chat, state
        )

    except Exception as e:
        logger.error("Ошибка при сохранении времени конца: %s", e, exc_info=True)
        text = "❌ Произошла ошибка при сохранении времени. Попробуйте позже."
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_work_hours_setting_ikb(),
            )
        await message.delete()


@router.message(WorkHoursState.waiting_tolerance_input)
async def tolerance_input_handler(message: Message, state: FSMContext) -> None:
    """Обработчик ввода отклонения"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    parsed_tolerance = parse_tolerance(text=message.text)

    if not parsed_tolerance:
        if active_message_id:
            text = (
                "❌ Неверный формат!\n\n"
                "Пожалуйста, пришлите положительное целое число (минуты).\n\n"
                "Например: 10"
            )
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
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
        updated_chat = await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(message.from_user.id),
            tolerance=parsed_tolerance,
        )

        if not updated_chat:
            text = "❌ Чат не найден. Попробуйте позже."
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=cancel_work_hours_setting_ikb(),
                )
            await message.delete()
            return

        success_message = Dialog.Chat.TOLERANCE_UPDATED.format(
            tolerance=parsed_tolerance
        )
        text = Dialog.Chat.WORK_HOURS_UPDATED.format(message=success_message)

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=cancel_work_hours_setting_ikb(),
        )

        await message.delete()

        # Возвращаемся в меню действий чата
        await _return_to_chat_actions(
            message.bot, message.chat.id, active_message_id, updated_chat, state
        )

    except Exception as e:
        logger.error("Ошибка при сохранении отклонения: %s", e, exc_info=True)
        text = "❌ Произошла ошибка при сохранении отклонения. Попробуйте позже."
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_work_hours_setting_ikb(),
            )
        await message.delete()


@router.callback_query(F.data == CallbackData.Chat.CANCEL_WORK_HOURS_SETTING)
async def cancel_work_hours_handler(
    callback: CallbackQuery,
    state: FSMContext,
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
            text=Dialog.Chat.CHAT_ACTIONS.format(
                title=chat.title,
                start_time=chat.start_time.strftime("%H:%M"),
                end_time=chat.end_time.strftime("%H:%M"),
            ),
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


async def _return_to_chat_actions(
    bot, chat_id: int, message_id: int, chat, state: FSMContext
) -> None:
    """Вспомогательная функция для возврата в меню действий чата"""
    try:
        await safe_edit_message(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            text=Dialog.Chat.CHAT_ACTIONS.format(
                title=chat.title,
                start_time=chat.start_time.strftime("%H:%M"),
                end_time=chat.end_time.strftime("%H:%M"),
            ),
            reply_markup=chat_actions_ikb(),
        )

        await state.set_state(ChatStateManager.selecting_chat)
    except Exception as e:
        logger.error("Ошибка при возврате в меню действий чата: %s", e, exc_info=True)
