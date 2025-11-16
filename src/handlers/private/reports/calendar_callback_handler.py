import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import CalendarKeyboard
from keyboards.inline.time_period import (
    time_period_ikb_all_users,
    time_period_ikb_chat,
    time_period_ikb_single_user,
)
from services.time_service import TimeZoneService
from states import AllUsersReportStates, ChatStateManager, SingleUserReportStates
from utils.exception_handler import handle_exception
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


async def handle_navigation(
    callback: CallbackQuery,
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

    calendar_kb = CalendarKeyboard.create_calendar(
        year=year,
        month=month,
        start_date=cal_start,
        end_date=cal_end,
    )

    text = "📅 Выберите начальную дату диапазона:"
    if cal_start:
        text = "📅 Выберите конечную дату диапазона:"

    await callback.message.edit_text(text=text, reply_markup=calendar_kb)


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

    if not cal_start or (cal_start and cal_end):
        await state.update_data(cal_start_date=selected_date, cal_end_date=None)

        calendar_kb = CalendarKeyboard.create_calendar(
            year=year,
            month=month,
            start_date=selected_date,
        )

        await callback.message.edit_text(
            text="📅 Выберите конечную дату диапазона:",
            reply_markup=calendar_kb,
        )
    else:
        if selected_date < cal_start:
            cal_start, selected_date = selected_date, cal_start

        await state.update_data(cal_start_date=cal_start, cal_end_date=selected_date)

        calendar_kb = CalendarKeyboard.create_calendar(
            year=year,
            month=month,
            start_date=cal_start,
            end_date=selected_date,
        )

        await callback.message.edit_text(
            text=f"✅ Выбран диапазон: {cal_start.strftime('%d.%m.%Y')} - {selected_date.strftime('%d.%m.%Y')}",
            reply_markup=calendar_kb,
        )


async def handle_reset(callback: CallbackQuery, state: FSMContext) -> None:
    """Сброс выбранных дат."""
    now = TimeZoneService.now()
    await state.update_data(cal_start_date=None, cal_end_date=None)

    calendar_kb = CalendarKeyboard.create_calendar(
        year=now.year,
        month=now.month,
    )

    await callback.message.edit_text(
        text="📅 Выберите начальную дату диапазона:",
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
    else:
        keyboard = time_period_ikb_single_user()

    await callback.message.edit_text(
        text="Выберите период для отчета",
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
        await callback.answer("⚠️ Выберите обе даты", show_alert=True)
        return

    current_state = await state.get_state()
    logger.info("Подтверждение выбора дат в state: %s", current_state)

    # В зависимости от state вызываем нужную функцию генерации отчета
    if current_state == ChatStateManager.selecting_custom_period:
        from .single_chat_report import generate_and_send_report

        await callback.message.delete()
        temp_message = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="⏳ Составляю отчёт...",
        )

        chat_id = user_data.get("chat_id")
        if not chat_id:
            logger.error("Отсутствует chat_id при confirm")
            await temp_message.delete()
            return

        await generate_and_send_report(
            message=temp_message,
            state=state,
            start_date=cal_start,
            end_date=cal_end,
            chat_id=chat_id,
            admin_tg_id=callback.from_user.id,
        )
        await log_and_set_state(
            message=temp_message,
            state=state,
            new_state=ChatStateManager.selecting_period,
        )

    elif current_state == SingleUserReportStates.selecting_custom_period:
        from .single_user_report import generate_and_send_report

        user_id = user_data.get("user_id")
        if not user_id:
            logger.error("Отсутствует user_id при confirm")
            await callback.answer(
                "❌ Ошибка: выберите пользователя заново", show_alert=True
            )
            return

        # Редактируем сообщение с календарем
        await callback.message.edit_text(text="⏳ Составляю отчёт...")

        await generate_and_send_report(
            callback=callback,
            state=state,
            user_id=user_id,
            start_date=cal_start,
            end_date=cal_end,
            admin_tg_id=callback.from_user.id,
        )

    elif current_state == AllUsersReportStates.selecting_custom_period:
        from .all_users_report import generate_and_send_report

        # Редактируем сообщение с календарем
        await callback.message.edit_text(text="⏳ Составляю отчёт...")

        await generate_and_send_report(
            callback=callback,
            state=state,
            start_date=cal_start,
            end_date=cal_end,
            admin_tg_id=callback.from_user.id,
        )


@router.callback_query(F.data.startswith("cal_"))
async def calendar_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Главный обработчик callback-кнопок календаря."""
    try:
        await callback.answer()

        data = callback.data.split("_")
        action = data[1]

        user_data = await state.get_data()
        cal_start = user_data.get("cal_start_date")
        cal_end = user_data.get("cal_end_date")

        if action == "ignore":
            return

        elif action in ("prev", "next"):
            year, month = int(data[2]), int(data[3])
            await handle_navigation(callback, action, year, month, cal_start, cal_end)

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
