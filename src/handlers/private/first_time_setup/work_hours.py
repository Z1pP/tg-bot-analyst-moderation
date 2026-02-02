import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users_chats_settings import (
    first_time_cancel_time_input_ikb,
    first_time_setup_success_ikb,
    first_time_work_hours_ikb,
)
from states import ChatStateManager
from states.first_time_setup import FirstTimeSetupStates
from usecases.chat import UpdateChatWorkHoursUseCase
from utils.data_parser import parse_breaks_time, parse_time, parse_tolerance
from utils.send_message import safe_edit_message

from .helpers import _show_time_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


# --- Work hours menu: show ENTER_* and wait for input ---
@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_WORK_START,
    StateFilter(FirstTimeSetupStates.waiting_work_start),
)
async def first_time_change_work_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    await state.update_data(active_message_id=callback.message.message_id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_WORK_START,
        reply_markup=first_time_cancel_time_input_ikb(),
    )
    await state.set_state(FirstTimeSetupStates.waiting_work_start_input)


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_WORK_END,
    StateFilter(FirstTimeSetupStates.waiting_work_start),
)
async def first_time_change_work_end(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    await state.update_data(active_message_id=callback.message.message_id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_WORK_END,
        reply_markup=first_time_cancel_time_input_ikb(),
    )
    await state.set_state(FirstTimeSetupStates.waiting_work_end_input)


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_TOLERANCE,
    StateFilter(FirstTimeSetupStates.waiting_work_start),
)
async def first_time_change_tolerance(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    await state.update_data(active_message_id=callback.message.message_id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_TOLERANCE,
        reply_markup=first_time_cancel_time_input_ikb(),
    )
    await state.set_state(FirstTimeSetupStates.waiting_tolerance_input)


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_CHANGE_BREAKS_TIME,
    StateFilter(FirstTimeSetupStates.waiting_work_start),
)
async def first_time_change_breaks_time(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    await state.update_data(active_message_id=callback.message.message_id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_BREAKS_TIME,
        reply_markup=first_time_cancel_time_input_ikb(),
    )
    await state.set_state(FirstTimeSetupStates.waiting_breaks_time_input)


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_CANCEL_TIME_INPUT,
    StateFilter(
        FirstTimeSetupStates.waiting_work_start_input,
        FirstTimeSetupStates.waiting_work_end_input,
        FirstTimeSetupStates.waiting_tolerance_input,
        FirstTimeSetupStates.waiting_breaks_time_input,
    ),
)
async def first_time_cancel_time_input(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    await _show_time_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        state=state,
    )


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_SAVE_AND_FINISH,
    StateFilter(FirstTimeSetupStates.waiting_work_start),
)
async def first_time_save_and_finish(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    await callback.answer()
    data = await state.get_data()
    chat_id = data.get("chat_id")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    tolerance = data.get("tolerance")
    breaks_time = data.get("breaks_time")
    if not all(
        [
            chat_id,
            start_time_str,
            end_time_str,
            tolerance is not None,
            breaks_time is not None,
        ]
    ):
        return
    start_time = (
        parse_time(start_time_str)
        if isinstance(start_time_str, str)
        else start_time_str
    )
    end_time = (
        parse_time(end_time_str) if isinstance(end_time_str, str) else end_time_str
    )
    usecase: UpdateChatWorkHoursUseCase = container.resolve(UpdateChatWorkHoursUseCase)
    try:
        await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(callback.from_user.id),
            start_time=start_time,
            end_time=end_time,
            tolerance=tolerance,
            breaks_time=breaks_time,
        )
    except Exception as e:
        logger.error("Ошибка при сохранении времени в визарде: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Ошибка при сохранении. Попробуйте позже.",
            reply_markup=first_time_work_hours_ikb(all_filled=True),
        )
        return
    saved_chat_id = chat_id
    await state.clear()
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.FIRST_TIME_SETUP_SUCCESS,
        reply_markup=first_time_setup_success_ikb(chat_id=saved_chat_id),
    )

    await state.set_state(ChatStateManager.listing_tracking_chats)


# --- Message handlers: input work start / end / tolerance / breaks ---
@router.message(FirstTimeSetupStates.waiting_work_start_input, F.text)
async def first_time_work_start_input(message: Message, state: FSMContext) -> None:
    parsed = parse_time(message.text)
    await message.delete()
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    if parsed is None:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Chat.WORK_START_INVALID_FORMAT,
            reply_markup=first_time_cancel_time_input_ikb(),
        )
        return
    await state.update_data(start_time=parsed.strftime("%H:%M"))
    await _show_time_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        state=state,
    )


@router.message(FirstTimeSetupStates.waiting_work_end_input, F.text)
async def first_time_work_end_input(message: Message, state: FSMContext) -> None:
    parsed = parse_time(message.text)
    await message.delete()
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    if parsed is None:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Chat.WORK_END_INVALID_FORMAT,
            reply_markup=first_time_cancel_time_input_ikb(),
        )
        return
    await state.update_data(end_time=parsed.strftime("%H:%M"))
    await _show_time_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        state=state,
    )


@router.message(FirstTimeSetupStates.waiting_tolerance_input, F.text)
async def first_time_tolerance_input(message: Message, state: FSMContext) -> None:
    parsed = parse_tolerance(message.text)
    await message.delete()
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    if parsed is None:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Chat.TOLERANCE_INVALID_FORMAT,
            reply_markup=first_time_cancel_time_input_ikb(),
        )
        return
    await state.update_data(tolerance=parsed)
    await _show_time_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        state=state,
    )


@router.message(FirstTimeSetupStates.waiting_breaks_time_input, F.text)
async def first_time_breaks_time_input(message: Message, state: FSMContext) -> None:
    parsed = parse_breaks_time(message.text)
    await message.delete()
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    if parsed is None:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Chat.BREAKS_TIME_INVALID_FORMAT,
            reply_markup=first_time_cancel_time_input_ikb(),
        )
        return
    await state.update_data(breaks_time=parsed)
    await _show_time_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        state=state,
    )
