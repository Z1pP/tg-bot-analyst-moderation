import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.period import TimePeriod
from container import container
from dto.report import AllUsersReportDTO
from keyboards.inline import CalendarKeyboard
from keyboards.inline.report import order_details_kb_all_users
from keyboards.inline.time_period import time_period_ikb_all_users
from keyboards.inline.users import all_users_actions_ikb
from services.time_service import TimeZoneService
from services.work_time_service import WorkTimeService
from states import AllUsersReportStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.report import GetAllUsersReportUseCase
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "back_from_period_all_users",
    AllUsersReportStates.selecting_period,
)
async def back_from_period_all_users_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата к действиям со всеми пользователями из выбора периода."""
    try:
        await callback.answer()
        # Очищаем данные отчета из state
        await state.update_data(all_users_report_dto=None)

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selected_all_users,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выбери действие:",
            reply_markup=all_users_actions_ikb(),
        )
    except Exception as e:
        await handle_exception(
            callback.message, e, "back_from_period_all_users_handler"
        )


@router.callback_query(
    F.data == "all_users",
    AllUsersReportStates.selecting_period,
)
async def back_to_period_selection_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата к выбору периода из детализации или отчета для всех пользователей."""
    try:
        await callback.answer()
        data = await state.get_data()
        all_users_report_dto = data.get("all_users_report_dto")

        if not all_users_report_dto:
            # Если нет данных отчета, возвращаемся к действиям
            await state.update_data(all_users_report_dto=None)
            await log_and_set_state(
                message=callback.message,
                state=state,
                new_state=AllUsersReportStates.selected_all_users,
            )
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="Выбери действие:",
                reply_markup=all_users_actions_ikb(),
            )
            return

        # Возвращаемся из детализации - показываем выбор периода
        logger.info(
            "Пользователь %s возвращается к выбору периода",
            callback.from_user.id,
        )

        # Проверяем наличие отслеживаемых чатов
        tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await tracked_chats_usecase.execute(
            tg_id=str(callback.from_user.id)
        )

        if not user_chats_dto.chats:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ У вас нет отслеживаемых чатов.\n"
                "Добавьте чаты в отслеживание для составления отчета.",
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых чатов",
                callback.from_user.username,
            )
            return

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selecting_period,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выберите период для отчета:",
            reply_markup=time_period_ikb_all_users(),
        )
    except Exception as e:
        await handle_exception(callback.message, e, "back_to_period_selection_handler")


@router.callback_query(
    F.data == "get_all_users_report",
    AllUsersReportStates.selected_all_users,
)
async def get_all_users_report_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик запроса на создание отчета по всем пользователям через callback."""
    try:
        await callback.answer()
        logger.info(
            "Пользователь %s запросил отчет по всем пользователям",
            callback.from_user.id,
        )

        # Проверяем наличие отслеживаемых чатов
        tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await tracked_chats_usecase.execute(
            tg_id=str(callback.from_user.id)
        )

        if not user_chats_dto.chats:
            await callback.message.edit_text(
                "❌ У вас нет отслеживаемых чатов.\n\n"
                "📋 <b>Как добавить чат в отслеживание:</b>\n"
                "1️⃣ Добавьте бота в нужный чат\n"
                "2️⃣ Дайте боту права администратора\n"
                "3️⃣ Напишите команду <code>/track</code> в чате\n\n"
                "После добавления чата вы сможете создавать отчеты."
            )
            logger.warning(
                "Админ %s пытается получить отчет без отслеживаемых чатов",
                callback.from_user.username,
            )
            return

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selecting_period,
        )

        await callback.message.edit_text(
            text="Выберите период для отчета:",
            reply_markup=time_period_ikb_all_users(),
        )
    except Exception as e:
        await handle_exception(
            callback.message, e, "get_all_users_report_callback_handler"
        )


@router.callback_query(
    AllUsersReportStates.selecting_period,
    F.data.startswith("period__"),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор периода для отчета через callback."""
    try:
        await callback.answer()
        period_text = callback.data.replace("period__", "")
        logger.info("Выбран период: %s", period_text)

        if period_text == TimePeriod.CUSTOM.value:
            logger.info("Запрос пользовательского периода")
            await log_and_set_state(
                message=callback.message,
                state=state,
                new_state=AllUsersReportStates.selecting_custom_period,
            )

            # Показываем календарь
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
            return

        start_date, end_date = TimePeriod.to_datetime(period_text)
        logger.info(f"Генерация отчета за период: {start_date} - {end_date}")

        await generate_and_send_report(
            callback=callback,
            state=state,
            start_date=start_date,
            end_date=end_date,
            selected_period=period_text,
        )
    except Exception as e:
        await handle_exception(callback.message, e, "process_period_selection_callback")


async def generate_and_send_report(
    callback: CallbackQuery,
    state: FSMContext,
    start_date: datetime,
    end_date: datetime,
    selected_period: str | None = None,
    admin_tg_id: int | None = None,
) -> None:
    """Генерирует и отправляет отчет."""
    try:
        logger.info(
            "Начало генерации отчета за период %s - %s",
            start_date,
            end_date,
        )

        adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
            start_date, end_date
        )

        report_dto = AllUsersReportDTO(
            user_tg_id=str(admin_tg_id or callback.from_user.id),
            start_date=adjusted_start,
            end_date=adjusted_end,
            selected_period=selected_period,
        )

        usecase: GetAllUsersReportUseCase = container.resolve(GetAllUsersReportUseCase)
        is_single_day = usecase.is_single_day_report(report_dto)
        report_parts = await usecase.execute(report_dto)

        # Сохраняем report_dto для детализации (только для многодневных отчетов)
        if not is_single_day:
            await state.update_data(all_users_report_dto=report_dto)

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selecting_period,
        )

        # Объединяем все части отчета в один текст
        full_report = "\n\n".join(report_parts)

        await callback.message.edit_text(
            text=full_report,
            parse_mode=ParseMode.HTML,
            reply_markup=order_details_kb_all_users(
                show_details=not is_single_day,
            ),
        )
        await callback.answer()

        logger.info("Отчет успешно отправлен пользователю")
    except Exception as e:
        logger.error(
            "Ошибка при генерации/отправке отчета: %s",
            e,
            exc_info=True,
        )
        await handle_exception(callback.message, e, "generate_and_send_report")
