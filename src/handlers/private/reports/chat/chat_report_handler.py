import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.period import TimePeriod
from dto.report import ChatReportDTO
from keyboards.inline import CalendarKeyboard
from keyboards.inline.chats import analytics_chat_actions_ikb, chat_actions_ikb
from keyboards.inline.report import order_details_kb_chat
from keyboards.inline.time_period import time_period_ikb_chat
from presenters import ReportPresenter
from services.time_service import TimeZoneService
from states import ChatStateManager, RatingStateManager
from usecases.report import GetChatReportUseCase
from utils.send_message import (
    safe_edit_message,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _show_analytics_chat_action_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает меню действий для аналитики по выбранному чату."""
    menu_text = (
        "Выберите действие:\n\n"
        '"Статистика" предоставит отчёт о работе отслеживаемых пользователях: '
        "кол-во сообщений, время ответов и реакций, перерывы и т.д.\n\n"
        '"Рейтинг активности" позволяет увидеть активность участников чата: '
        'кол-во "живых" юзеров, топ по сообщениям и реакциям\n\n'
        '"AI-сводка" кратко и детально расскажет о том, что происходило в чате '
        "за последние 1К сообщений\n\n"
        "❗️Больше информации о настройках чата в FAQ на сайте Analyst AI"
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=analytics_chat_actions_ikb(),
    )

    await state.set_state(ChatStateManager.selecting_chat_report_action)


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_CHAT),
    ChatStateManager.selecting_chat_for_report,
)
async def analytics_chat_selected_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор чата для аналитики."""
    await callback.answer()

    chat_id_str = callback.data.replace(CallbackData.Chat.PREFIX_CHAT, "")
    if not chat_id_str.isdigit():
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chat_actions_ikb(),
        )
        return

    await state.update_data(chat_id=int(chat_id_str))
    await _show_analytics_chat_action_menu(callback=callback, state=state)


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
    ChatStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
    ChatStateManager.selecting_custom_period,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
    ChatStateManager.selecting_chat_report_action,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
    RatingStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS,
    RatingStateManager.selecting_custom_period,
)
async def back_to_analytics_chat_actions_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Возврат к меню действий аналитики по чату."""
    await callback.answer()
    await _show_analytics_chat_action_menu(callback=callback, state=state)


@router.callback_query(
    F.data == CallbackData.Chat.GET_REPORT,
    ChatStateManager.selecting_chat_report_action,
)
async def get_chat_report_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик запроса на создание отчета по выбранному чату."""
    await callback.answer()

    # Проверка tracked_users перенесена в UseCase
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.SELECT_PERIOD,
        reply_markup=time_period_ikb_chat(
            back_callback=CallbackData.Chat.BACK_TO_ANALYTICS_CHAT_ACTIONS
        ),
    )

    await state.set_state(ChatStateManager.selecting_period)


@router.callback_query(
    F.data.startswith(CallbackData.Report.PREFIX_PERIOD),
    ChatStateManager.selecting_period,
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обрабатывает выбор периода для отчета по чату через callback."""
    await callback.answer()

    period_text = callback.data.replace(CallbackData.Report.PREFIX_PERIOD, "")
    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
        )
        return

    logger.info(
        "Пользователь %s выбрал период %s для чата %s",
        callback.from_user.username,
        chat_id,
        period_text,
    )

    if period_text == TimePeriod.CUSTOM.value:
        await state.set_state(ChatStateManager.selecting_custom_period)

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
        container=container,
    )


async def _render_report_view(
    callback: CallbackQuery,
    state: FSMContext,
    chat_id: int,
    container: Container,
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
        container: Контейнер зависимостей
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
        await state.update_data(chat_report_dto=report_dto.model_dump(mode="json"))

    # Объединяем все части отчета в один текст
    full_report = "\n\n".join(report_parts)
    if not result.is_single_day:
        full_report = f"{full_report}{Dialog.Report.CONTINUE_SELECT_PERIOD}"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=full_report,
        reply_markup=order_details_kb_chat(
            show_details=not result.is_single_day,
            back_to_period_callback=CallbackData.Report.BACK_TO_PERIODS,
        ),
    )

    await state.set_state(ChatStateManager.selecting_period)
