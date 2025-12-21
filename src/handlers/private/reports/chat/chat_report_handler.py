import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.period import SummaryTimePeriod, TimePeriod
from container import container
from dto.report import ChatReportDTO
from keyboards.inline import CalendarKeyboard
from keyboards.inline.chats import chat_actions_ikb
from keyboards.inline.report import hide_details_ikb, order_details_kb_chat
from keyboards.inline.time_period import time_period_ikb_chat
from presenters import ReportPresenter
from services.chat import ChatService
from services.time_service import TimeZoneService
from states import ChatStateManager
from usecases.report import GetChatReportUseCase
from usecases.summarize.summarize_chat_messages import GetChatSummaryUseCase
from utils.send_message import safe_edit_message, send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.GET_STATISTICS,
    ChatStateManager.selecting_chat,
)
async def get_chat_statistics_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик запроса на создание отчета по конкретному чату."""
    await callback.answer()

    # Проверка tracked_users перенесена в UseCase
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_chat(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_period,
    )


@router.callback_query(
    F.data == CallbackData.Chat.GET_CHAT_SUMMARY_24H,
    ChatStateManager.selecting_chat,
)
async def process_get_chat_summary_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик запроса на генерацию ИИ-сводки по чату за последние 24 часа."""
    await callback.answer()

    data = await state.get_data()
    chat_id = data.get("chat_id")
    user_id = callback.from_user.id

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chat_actions_ikb(),
        )
        return

    # Получаем информацию о чате для возврата к dashboard
    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    # 1. Показываем статус выполнения в текущем сообщении
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="⏳ <b>Сводка на этапе выполнения</b>\nПожалуйста, подождите, это может занять до 30 секунд...",
    )

    try:
        # 2. Подготовка дат для 24ч
        start_date, end_date = SummaryTimePeriod.to_datetime(
            SummaryTimePeriod.LAST_24_HOURS.value
        )

        # 3. Вызываем UseCase
        usecase: GetChatSummaryUseCase = container.resolve(GetChatSummaryUseCase)
        summary = await usecase.execute(
            user_id=user_id,
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 4. Отправляем ОТДЕЛЬНОЕ сообщение с результатом и кнопкой "Скрыть"
        sent_message = await send_html_message_with_kb(
            message=callback.message,
            text=summary,
        )

        # Добавляем кнопку "Скрыть" (удаляет это сообщение)
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=sent_message.message_id,
            reply_markup=hide_details_ikb([sent_message.message_id]),
        )

        # 5. Возвращаем исходное сообщение к виду Dashboard
        if chat:
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
        else:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="✅ Сводка готова! Она отправлена отдельным сообщением.",
                reply_markup=chat_actions_ikb(),
            )

    except Exception as e:
        logger.error(
            f"Ошибка при генерации сводки для чата {chat_id}: {e}", exc_info=True
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Произошла ошибка при генерации сводки. Попробуйте позже.",
            reply_markup=chat_actions_ikb(),
        )


@router.callback_query(
    ChatStateManager.selecting_period,
    F.data.startswith(CallbackData.Report.PREFIX_PERIOD),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор периода для отчета по чату через callback."""
    await callback.answer()

    period_text = callback.data.replace(CallbackData.Report.PREFIX_PERIOD, "")
    data = await state.get_data()
    chat_id = data.get("chat_id")

    logger.info(
        "Пользователь %s выбрал период %s для чата %s",
        callback.from_user.username,
        chat_id,
        period_text,
    )

    if period_text == TimePeriod.CUSTOM.value:
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=ChatStateManager.selecting_custom_period,
        )

        # Показываем календарь
        now = TimeZoneService.now()
        await state.update_data(cal_start_date=None, cal_end_date=None)

        calendar_kb = CalendarKeyboard.create_calendar_chat(
            year=now.year,
            month=now.month,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.SELECT_START_DATE,
            reply_markup=calendar_kb,
        )
        return

    await _render_report_view(
        callback=callback,
        state=state,
        chat_id=chat_id,
        period_text=period_text,
    )


async def _render_report_view(
    callback: CallbackQuery,
    state: FSMContext,
    chat_id: int,
    period_text: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> None:
    """
    Presentation Layer: форматирует и отправляет отчет пользователю.
    Управляет FSM состоянием и клавиатурами.

    Args:
        callback: Callback query
        state: FSM context
        chat_id: ID чата
        period_text: Текстовый период (например, "today", "yesterday")
        start_date: Начальная дата для кастомного периода (из календаря)
        end_date: Конечная дата для кастомного периода (из календаря)
    """
    # Для кастомных дат из календаря используем специальный период
    selected_period = period_text or TimePeriod.CUSTOM.value

    report_dto = ChatReportDTO(
        chat_id=chat_id,
        admin_tg_id=str(callback.from_user.id),
        selected_period=selected_period,
        start_date=start_date,
        end_date=end_date,
    )

    try:
        usecase: GetChatReportUseCase = container.resolve(GetChatReportUseCase)
        result = await usecase.execute(dto=report_dto)
    except Exception as e:
        logger.error(
            "Ошибка при генерации отчета по чату %s: %s",
            chat_id,
            e,
            exc_info=True,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GENERATING_REPORT,
            reply_markup=chat_actions_ikb(),
        )
        return

    # Форматируем результат через Presenter
    presenter = ReportPresenter()
    report_parts = presenter.format_report(result)

    if result.error_message:
        # Если есть ошибка, presenter уже вернул её в report_parts
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=report_parts[0] if report_parts else result.error_message,
            reply_markup=chat_actions_ikb(),
        )
        return

    # Сохраняем report_dto для детализации (только для многодневных отчетов)
    if not result.is_single_day:
        await state.update_data(chat_report_dto=report_dto)

    # Объединяем все части отчета в один текст
    full_report = "\n\n".join(report_parts)
    if not result.is_single_day:
        full_report = f"{full_report}{Dialog.Report.CONTINUE_SELECT_PERIOD}"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=full_report,
        reply_markup=order_details_kb_chat(show_details=not result.is_single_day),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_period,
    )
