from aiogram import Bot
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.users_chats_settings import (
    first_time_setup_ikb,
    first_time_work_hours_ikb,
)
from states.first_time_setup import FirstTimeSetupStates
from utils.send_message import safe_edit_message


async def _show_error_and_stay(
    bot: Bot,
    chat_id: int,
    active_message_id: int | None,
    text: str,
    reply_markup=None,
) -> None:
    """
    Показывает ошибку в текущем сообщении визарда и оставляет состояние без перехода.
    Если active_message_id задан — редактирует это сообщение, иначе отправляет новое.
    """
    markup = reply_markup if reply_markup is not None else first_time_setup_ikb()
    if active_message_id is not None:
        await safe_edit_message(
            bot=bot,
            chat_id=chat_id,
            message_id=active_message_id,
            text=text,
            reply_markup=markup,
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
        )


def _build_first_time_work_hours_view(state_data: dict) -> str:
    """Формирует текст экрана настройки времени из данных state (указанные/не указанные)."""
    start_time = state_data.get("start_time")
    end_time = state_data.get("end_time")
    tolerance = state_data.get("tolerance")
    breaks_time = state_data.get("breaks_time")
    has_any = (
        start_time is not None
        or end_time is not None
        or tolerance is not None
        or breaks_time is not None
    )
    if has_any:
        return Dialog.Chat.TIME_REPORT_EXISTS.format(
            start_time=start_time if start_time else "не указано",
            end_time=end_time if end_time else "не указано",
            tolerance=tolerance if tolerance is not None else "не указано",
            breaks_time=breaks_time if breaks_time is not None else "не указано",
        )
    return Dialog.Chat.TIME_REPORT_NOT_EXISTS


async def _show_time_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
) -> None:
    """Показывает экран меню времени (текст + клавиатура с кнопкой Сохранить только при всех заполненных)."""
    data = await state.get_data()
    all_filled = (
        data.get("start_time") is not None
        and data.get("end_time") is not None
        and data.get("tolerance") is not None
        and data.get("breaks_time") is not None
    )
    text = _build_first_time_work_hours_view(data)
    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=first_time_work_hours_ikb(all_filled=all_filled),
    )
    await state.set_state(FirstTimeSetupStates.waiting_work_start)
