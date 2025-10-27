import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from constants.period import TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.inline import CalendarKeyboard, order_details_kb
from keyboards.reply import admin_menu_kb, chat_actions_kb, get_time_period_kb
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import ChatStateManager
from usecases.report import GetReportOnSpecificChatUseCase
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    ChatStateManager.selecting_chat,
    F.text == KbCommands.GET_REPORT,
)
async def single_chat_report_handler(message: Message, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await select_chat_again(message=message, state=state)
            return
        logger.info(
            "Пользователь %s запросил отчет по чату %s",
            message.from_user.username,
            chat_id,
        )

        tracked_users_usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        tracked_users = await tracked_users_usecase.execute(
            admin_tgid=str(message.from_user.id)
        )

        if not tracked_users:
            await message.answer(
                "❌ У вас нет отслеживаемых пользователей.\n"
                "Добавьте пользователей в отслеживание для составления отчета.",
                reply_markup=chat_actions_kb(),
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых пользователей",
                message.from_user.username,
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_period,
        )

        await send_html_message_with_kb(
            text="Выберите период для отчета",
            message=message,
            reply_markup=get_time_period_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "specific_chat_report")


@router.message(
    ChatStateManager.selecting_period,
    F.text.in_(TimePeriod.get_all_periods()),
)
async def process_report_input(message: Message, state: FSMContext) -> None:
    """Обрабатывает выбор периода для отчета."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        logger.info(
            "Выбран период для чата %s: %s",
            chat_id,
            message.text,
        )

        if not chat_id:
            logger.warning("Отсутствует название чата при выборе периода")
            await select_chat_again(message=message, state=state)
            return

        if message.text == TimePeriod.CUSTOM.value:
            await log_and_set_state(
                message=message,
                state=state,
                new_state=ChatStateManager.selecting_custom_period,
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

        start_date, end_date = TimePeriod.to_datetime(message.text)
        logger.info(
            "Генерация отчета по чату %s за период: %s - %s",
            chat_id,
            start_date,
            end_date,
        )

        await generate_and_send_report(
            message=message,
            state=state,
            start_date=start_date,
            end_date=end_date,
            chat_id=chat_id,
            selected_period=message.text,
        )
    except Exception as e:
        await handle_exception(message, e, "process_report_input")


@router.callback_query(
    F.data.startswith("cal_"), ChatStateManager.selecting_custom_period
)
async def calendar_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик callback-кнопок календаря."""
    try:
        await callback.answer()

        data = callback.data.split("_")
        action = data[1]

        user_data = await state.get_data()
        cal_start = user_data.get("cal_start_date")
        cal_end = user_data.get("cal_end_date")
        chat_id = user_data.get("chat_id")

        if not chat_id:
            await select_chat_again(callback.message, state)
            return

        if action == "ignore":
            return

        elif action == "prev" or action == "next":
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
            year, month, day = int(data[2]), int(data[3]), int(data[4])
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
            if cal_start and cal_end:
                await callback.message.delete()

                temp_message = await callback.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text="⏳ Генерирую отчёт...",
                )

                await generate_and_send_report(
                    message=temp_message,
                    state=state,
                    start_date=cal_start,
                    end_date=cal_end,
                    chat_id=chat_id,
                    admin_tg_id=callback.from_user.id,
                )

                await temp_message.delete()
                await state.set_state(ChatStateManager.selecting_period)

        elif action == "reset":
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
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="Выбор периода отменён",
                reply_markup=get_time_period_kb(),
            )

    except Exception as e:
        await handle_exception(callback.message, e, "calendar_callback_handler")


@router.message(
    ChatStateManager.selecting_period,
    F.text == KbCommands.BACK,
)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для возврата в меню чата."""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await select_chat_again(message=message, state=state)
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_chat,
        )

        await send_html_message_with_kb(
            message=message,
            text="Возврат к меню чата.",
            reply_markup=chat_actions_kb(),
        )
    except Exception as e:
        await handle_exception(message, e, "back_to_menu_handler")


async def select_chat_again(message: Message, state: FSMContext) -> None:
    """Повторно запрашивает выбор чата."""

    logger.info("Запрос повторного выбора чата")
    await log_and_set_state(
        message=message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )
    await send_html_message_with_kb(
        message=message,
        text="Выберите чат заново",
        reply_markup=admin_menu_kb(),
    )


async def generate_and_send_report(
    message: Message,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    chat_id: int,
    selected_period: Optional[str] = None,
    admin_tg_id: Optional[int] = None,
) -> None:
    """Генерирует и отправляет отчет по чату."""
    try:
        logger.info(
            "Начало генерации отчета по чату %s за период %s - %s",
            chat_id,
            start_date,
            end_date,
        )

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = ChatReportDTO(
            chat_id=chat_id,
            admin_tg_id=str(admin_tg_id or message.from_user.id),
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        usecase: GetReportOnSpecificChatUseCase = container.resolve(
            GetReportOnSpecificChatUseCase
        )
        is_single_day = usecase.is_single_day_report(report_dto)
        report_parts = await usecase.execute(dto=report_dto)

        logger.info(
            "Отчет по чату %s сгенерирован, частей: %s",
            chat_id,
            len(report_parts),
        )

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not is_single_day:
            await state.update_data(chat_report_dto=report_dto)

        await state.set_state(ChatStateManager.selecting_period)

        for idx, part in enumerate(report_parts):
            if idx == len(report_parts) - 1:
                part = f"{part}\n\nДля продолжения выберите период, либо нажмите назад"

            await send_html_message_with_kb(
                message=message,
                text=part,
                reply_markup=order_details_kb(show_details=not is_single_day),
            )

        logger.info("Отчет по чату %s успешно отправлен", chat_id)
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета по чату %s: %s",
            chat_id,
            e,
            exc_info=True,
        )
        await handle_exception(message, e, "generate_and_send_report")
