import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import SingleUserReportDTO
from keyboards.inline import CalendarKeyboard, order_details_kb
from keyboards.reply import admin_menu_kb, get_time_period_kb
from keyboards.reply.user_actions import user_actions_kb
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import SingleUserReportStates
from usecases.report import GetSingleUserReportUseCase

from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _validate_user_id(message: Message, state: FSMContext) -> Optional[int]:
    """Валидирует наличие user_id в состоянии."""
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await send_html_message_with_kb(
            message=message,
            text="Выберите пользователя заново",
            reply_markup=admin_menu_kb(),
        )

    return user_id


@router.message(
    F.text == KbCommands.GET_REPORT,
    SingleUserReportStates.selected_single_user,
)
async def single_user_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета о времени ответа."""
    try:
        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selecting_period,
        )

        await send_html_message_with_kb(
            message=message,
            text="Выберите период для отчета",
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "single_user_report_handler")


@router.message(
    SingleUserReportStates.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_period_selection(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета о времени ответа."""
    try:
        user_id = await _validate_user_id(message, state)
        if not user_id:
            return

        if message.text == TimePeriod.CUSTOM.value:
            await log_and_set_state(
                message=message,
                state=state,
                new_state=SingleUserReportStates.waiting_cutom_period,
            )

            # Показываем календарь
            now = TimeZoneService.now()
            await state.update_data(cal_start_date=None, cal_end_date=None)

            calendar_kb = CalendarKeyboard.create_calendar(
                year=now.year,
                month=now.month,
            )

            await message.answer(
                text="📅 Выберите начальную дату диапазона:",
                reply_markup=calendar_kb,
            )
            return

        start_date, end_date = TimePeriod.to_datetime(period=message.text)
        await _generate_and_send_report(
            message=message,
            state=state,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_period_selection")


@router.message(
    SingleUserReportStates.selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в меню пользователя."""
    try:
        user_id = await _validate_user_id(message, state)
        if not user_id:
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selected_single_user,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в меню",
            reply_markup=user_actions_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


@router.callback_query(F.data.startswith("cal_"))
async def calendar_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик callback-кнопок календаря."""
    try:
        await callback.answer()

        data = callback.data.split("_")
        action = data[1]

        user_data = await state.get_data()
        cal_start = user_data.get("cal_start_date")
        cal_end = user_data.get("cal_end_date")

        if action == "ignore":
            return

        elif action == "prev" or action == "next":
            # Перелистывание месяца
            year, month = int(data[2]), int(data[3])

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

            await callback.message.edit_text(
                text=text,
                reply_markup=calendar_kb,
            )

        elif action == "day":
            # Выбор дня
            year, month, day = int(data[2]), int(data[3]), int(data[4])
            selected_date = datetime(year, month, day)

            if not cal_start or (cal_start and cal_end):
                # Выбираем начальную дату
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
                # Выбираем конечную дату
                if selected_date < cal_start:
                    # Меняем местами
                    cal_start, selected_date = selected_date, cal_start

                await state.update_data(
                    cal_start_date=cal_start, cal_end_date=selected_date
                )

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

        elif action == "confirm":
            # Подтверждение выбора
            if cal_start and cal_end:
                user_id = await _validate_user_id(callback.message, state)
                if not user_id:
                    return

                await callback.message.delete()

                # Создаём временное сообщение для передачи в функцию
                temp_message = await callback.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text="⏳ Генерирую отчёт...",
                )

                await _generate_and_send_report(
                    message=temp_message,
                    state=state,
                    user_id=user_id,
                    start_date=cal_start,
                    end_date=cal_end,
                    admin_tg_id=callback.from_user.id,
                )

                await temp_message.delete()

                await state.set_state(SingleUserReportStates.selecting_period)

        elif action == "reset":
            # Сброс выбора
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

        elif action == "cancel":
            # Отмена
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="Выбор периода отменён",
                reply_markup=get_time_period_kb(),
            )

    except Exception as e:
        await handle_exception(callback.message, e, "calendar_callback_handler")


async def _generate_and_send_report(
    message: Message,
    state: FSMContext,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    selected_period: Optional[str] = None,
    admin_tg_id: Optional[int] = None,
) -> None:
    """Генерирует и отправляет отчет."""
    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date, end_date
    )

    report_dto = SingleUserReportDTO(
        user_id=user_id,
        admin_tg_id=str(admin_tg_id or message.from_user.id),
        start_date=adjusted_start,
        end_date=adjusted_end,
        selected_period=selected_period,
    )

    usecase: GetSingleUserReportUseCase = container.resolve(GetSingleUserReportUseCase)
    is_single_day = usecase.is_single_day_report(report_dto)
    report_parts = await usecase.execute(report_dto=report_dto)

    # Сохраняем report_dto для детализации (только для многодневных отчетов)
    if not is_single_day:
        await state.update_data(report_dto=report_dto)

    for idx, part in enumerate(report_parts):
        if idx == len(report_parts) - 1:
            part = f"{part}"

        await send_html_message_with_kb(
            message=message,
            text=part,
            reply_markup=order_details_kb(show_details=not is_single_day),
        )
