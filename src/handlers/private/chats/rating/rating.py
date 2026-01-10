import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.period import TimePeriod
from keyboards.inline.calendar_kb import CalendarKeyboard
from keyboards.inline.chats import chat_actions_ikb, rating_report_ikb
from keyboards.inline.time_period import time_period_ikb_chat
from presenters.rating_presenter import RatingPresenter
from services.time_service import TimeZoneService
from states import RatingStateManager
from usecases.report.daily_rating import GetDailyTopUsersUseCase
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.GET_DAILY_RATING)
async def chat_daily_rating_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик для показа рейтинга выбранного чата за сутки."""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Rating.SELECT_PERIOD,
        reply_markup=time_period_ikb_chat(),
    )

    await state.set_state(RatingStateManager.selecting_period)


@router.callback_query(
    RatingStateManager.selecting_period,
    F.data.startswith(CallbackData.Report.PREFIX_PERIOD),
)
async def process_period_selection_callback(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обрабатывает выбор периода для рейтинга чата через callback."""
    await callback.answer()

    period_text = callback.data.replace(CallbackData.Report.PREFIX_PERIOD, "")
    data = await state.get_data()
    chat_id = data.get("chat_id")

    logger.info(
        "Пользователь %s выбрал период для рейтинга %s для чата %s",
        callback.from_user.username,
        period_text,
        chat_id,
    )

    if period_text == TimePeriod.CUSTOM.value:
        await state.set_state(RatingStateManager.selecting_custom_period)

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

    # Получаем диапазон дат для выбранного периода
    try:
        start_date, end_date = TimePeriod.to_datetime(period_text)
    except Exception as e:
        logger.error("Ошибка при получении дат для периода %s: %s", period_text, e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Report.ERROR_GENERATING_REPORT,
            reply_markup=chat_actions_ikb(),
        )
        return

    await _render_rating_view(
        callback=callback,
        state=state,
        chat_id=chat_id,
        start_date=start_date,
        end_date=end_date,
        container=container,
    )


async def _render_rating_view(
    callback: CallbackQuery,
    state: FSMContext,
    chat_id: int,
    start_date: datetime,
    end_date: datetime,
    container: Container,
) -> None:
    """Рендерит представление рейтинга чата."""
    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Report.GENERATING_REPORT,
    )

    try:
        usecase: GetDailyTopUsersUseCase = container.resolve(GetDailyTopUsersUseCase)
        stats = await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(callback.from_user.id),
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.error("Ошибка при получении рейтинга чата: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GETTING_RATING,
            reply_markup=chat_actions_ikb(),
        )
        return

    try:
        # Форматируем рейтинг
        rating_text = RatingPresenter.format_daily_rating(stats)
    except Exception as e:
        logger.error("Ошибка при форматировании рейтинга чата: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_FORMATTING_RATING,
            reply_markup=chat_actions_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=rating_text,
        reply_markup=rating_report_ikb(),
    )
