import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.period import TimePeriod
from keyboards.inline import CalendarKeyboard
from keyboards.inline.time_period import (
    time_period_ikb_all_users,
    time_period_ikb_chat,
    time_period_ikb_single_user,
)
from services.time_service import TimeZoneService
from states import (
    AllUsersReportStates,
    ChatStateManager,
    RatingStateManager,
    SingleUserReportStates,
)
from utils.exception_handler import handle_exception

router = Router()
logger = logging.getLogger(__name__)


async def handle_navigation(
    callback: CallbackQuery,
    state: FSMContext,
    action: str,
    year: int,
    month: int,
    cal_start: datetime,
    cal_end: datetime,
) -> None:
    """Обработка навигации по календарю (prev/next)."""
    if action == "prev":
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    else:
        month += 1
        if month > 12:
            month = 1
            year += 1

    current_state = await state.get_state()
    calendar_kb = _create_calendar_by_state(
        current_state=current_state,
        year=year,
        month=month,
        start_date=cal_start,
        end_date=cal_end,
    )

    text = Dialog.Calendar.SELECT_START_DATE
    if cal_start:
        text = Dialog.Calendar.SELECT_END_DATE

    await callback.message.edit_text(text=text, reply_markup=calendar_kb)


def _create_calendar_by_state(
    current_state,
    year: int,
    month: int,
    start_date: datetime,
    end_date: datetime = None,
):
    """Создает календарь в зависимости от текущего состояния."""
    if current_state == SingleUserReportStates.selecting_custom_period:
        return CalendarKeyboard.create_calendar_single_user(
            year=year, month=month, start_date=start_date, end_date=end_date
        )
    elif current_state == AllUsersReportStates.selecting_custom_period:
        return CalendarKeyboard.create_calendar_all_users(
            year=year, month=month, start_date=start_date, end_date=end_date
        )
    elif current_state == ChatStateManager.selecting_custom_period:
        return CalendarKeyboard.create_calendar_chat(
            year=year, month=month, start_date=start_date, end_date=end_date
        )
    elif current_state == RatingStateManager.selecting_custom_period:
        return CalendarKeyboard.create_calendar_chat(
            year=year, month=month, start_date=start_date, end_date=end_date
        )
    return None


async def handle_day_selection(
    callback: CallbackQuery,
    state: FSMContext,
    year: int,
    month: int,
    day: int,
    cal_start: datetime,
    cal_end: datetime,
) -> None:
    """Обработка выбора дня в календаре."""
    selected_date = datetime(year, month, day)

    current_state = await state.get_state()

    if not cal_start or cal_end:
        await state.update_data(
            cal_start_date=selected_date.isoformat(), cal_end_date=None
        )

        calendar_kb = _create_calendar_by_state(
            current_state=current_state,
            year=year,
            month=month,
            start_date=selected_date,
        )

        await callback.message.edit_text(
            text=Dialog.Calendar.SELECT_END_DATE,
            reply_markup=calendar_kb,
        )
        return

    if cal_start and selected_date < cal_start:
        cal_start, selected_date = selected_date, cal_start

    await state.update_data(
        cal_start_date=cal_start.isoformat(), cal_end_date=selected_date.isoformat()
    )

    calendar_kb = _create_calendar_by_state(
        current_state=current_state,
        year=year,
        month=month,
        start_date=cal_start,
        end_date=selected_date,
    )

    await callback.message.edit_text(
        text=Dialog.Report.DATE_RANGE_SELECTED.format(
            start_date=cal_start.strftime("%d.%m.%Y"),
            end_date=selected_date.strftime("%d.%m.%Y"),
        ),
        reply_markup=calendar_kb,
    )


async def handle_reset(callback: CallbackQuery, state: FSMContext) -> None:
    """Сброс выбранных дат."""
    now = TimeZoneService.now()
    await state.update_data(cal_start_date=None, cal_end_date=None)

    current_state = await state.get_state()
    if current_state == SingleUserReportStates.selecting_custom_period:
        calendar_kb = CalendarKeyboard.create_calendar_single_user(
            year=now.year,
            month=now.month,
        )
    elif current_state == AllUsersReportStates.selecting_custom_period:
        calendar_kb = CalendarKeyboard.create_calendar_all_users(
            year=now.year,
            month=now.month,
        )
    elif current_state == ChatStateManager.selecting_custom_period:
        calendar_kb = CalendarKeyboard.create_calendar_chat(
            year=now.year,
            month=now.month,
        )
    elif current_state == RatingStateManager.selecting_custom_period:
        calendar_kb = CalendarKeyboard.create_calendar_chat(
            year=now.year,
            month=now.month,
        )

    await callback.message.edit_text(
        text=Dialog.Calendar.SELECT_START_DATE,
        reply_markup=calendar_kb,
    )


async def handle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена выбора периода."""

    current_state = await state.get_state()

    # Выбираем клавиатуру в зависимости от состояния
    if current_state == SingleUserReportStates.selecting_custom_period:
        keyboard = time_period_ikb_single_user()
    elif current_state == AllUsersReportStates.selecting_custom_period:
        keyboard = time_period_ikb_all_users()
    elif current_state == ChatStateManager.selecting_custom_period:
        keyboard = time_period_ikb_chat()
    elif current_state == RatingStateManager.selecting_custom_period:
        keyboard = time_period_ikb_chat()

    await callback.message.edit_text(
        text=Dialog.Calendar.SELECT_PERIOD,
        reply_markup=keyboard,
    )


async def handle_confirm_action(
    callback: CallbackQuery,
    state: FSMContext,
    cal_start: datetime,
    cal_end: datetime,
    user_data: dict,
) -> None:
    """Обработка подтверждения выбора дат - вызов генерации отчета."""
    if not (cal_start and cal_end):
        await callback.answer(Dialog.Calendar.SELECT_BOTH_DATES, show_alert=True)
        return

    current_state = await state.get_state()
    logger.info("Подтверждение выбора дат в state: %s", current_state)

    # В зависимости от state вызываем нужную функцию генерации отчета
    if current_state == ChatStateManager.selecting_custom_period:
        from .chat.chat_report_handler import _render_report_view

        chat_id = user_data.get("chat_id")
        if not chat_id:
            await callback.answer(
                Dialog.Report.ERROR_SELECT_CHAT_AGAIN, show_alert=True
            )
            return

        await callback.message.edit_text(text=Dialog.Calendar.GENERATING_REPORT)

        await _render_report_view(
            callback=callback,
            state=state,
            chat_id=chat_id,
            start_date=cal_start,
            end_date=cal_end,
        )

    elif current_state == RatingStateManager.selecting_custom_period:
        from ..chats.rating.rating import _render_rating_view

        chat_id = user_data.get("chat_id")
        if not chat_id:
            await callback.answer(Dialog.Chat.CHAT_NOT_SELECTED, show_alert=True)
            return

        await _render_rating_view(
            callback=callback,
            state=state,
            chat_id=chat_id,
            start_date=cal_start,
            end_date=cal_end,
        )

    elif current_state == SingleUserReportStates.selecting_custom_period:
        from .single_user.single_user_report_handler import _render_report_view

        user_id = user_data.get("user_id")
        if not user_id:
            logger.error("Отсутствует user_id при confirm")
            await callback.answer(
                Dialog.Report.ERROR_SELECT_USER_AGAIN, show_alert=True
            )
            return

        # Редактируем сообщение с календарем
        await callback.message.edit_text(text=Dialog.Calendar.GENERATING_REPORT)

        await _render_report_view(
            callback=callback,
            state=state,
            user_id=user_id,
            start_date=cal_start,
            end_date=cal_end,
            selected_period=TimePeriod.CUSTOM.value,
        )

    elif current_state == AllUsersReportStates.selecting_custom_period:
        from .all_users.all_users_report_handler import _render_all_users_report

        # Редактируем сообщение с календарем
        await callback.message.edit_text(text=Dialog.Calendar.GENERATING_REPORT)

        await _render_all_users_report(
            callback=callback,
            state=state,
            start_date=cal_start,
            end_date=cal_end,
            selected_period=TimePeriod.CUSTOM.value,
        )


@router.callback_query(F.data.startswith(CallbackData.Report.PREFIX_CALENDAR))
async def calendar_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Главный обработчик callback-кнопок календаря."""
    try:
        await callback.answer()

        data = callback.data.split("_")
        action = data[1]

        user_data = await state.get_data()
        cal_start = user_data.get("cal_start_date")
        cal_end = user_data.get("cal_end_date")

        cal_start = (
            datetime.fromisoformat(cal_start)
            if isinstance(cal_start, str)
            else cal_start
        )
        cal_end = (
            datetime.fromisoformat(cal_end) if isinstance(cal_end, str) else cal_end
        )

        if action == "ignore":
            return

        elif action in ("prev", "next"):
            year, month = int(data[2]), int(data[3])
            await handle_navigation(
                callback=callback,
                state=state,
                action=action,
                year=year,
                month=month,
                cal_start=cal_start,
                cal_end=cal_end,
            )

        elif action == "day":
            year, month, day = int(data[2]), int(data[3]), int(data[4])
            await handle_day_selection(
                callback, state, year, month, day, cal_start, cal_end
            )

        elif action == "reset":
            await handle_reset(callback, state)

        elif action == "cancel":
            await handle_cancel(callback, state)

        elif action == "confirm":
            await handle_confirm_action(callback, state, cal_start, cal_end, user_data)

    except Exception as e:
        await handle_exception(callback.message, e, "calendar_callback_handler")
