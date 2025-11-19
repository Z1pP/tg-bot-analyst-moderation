import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats_kb import chat_actions_ikb
from usecases.report.daily_rating import GetDailyTopUsersUseCase
from utils.rating_formatter import RatingFormatter
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.GET_DAILY_RATING)
async def chat_daily_rating_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик для показа рейтинга выбранного чата за сутки."""
    await callback.answer()

    data = await state.get_data()
    chat_id = data.get("chat_id")

    logger.info(
        "Пользователь %s начал получение рейтинга чата %s",
        callback.from_user.username,
        chat_id,
    )

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return
    try:
        usecase: GetDailyTopUsersUseCase = container.resolve(GetDailyTopUsersUseCase)
        stats = await usecase.execute(chat_id=chat_id, date=datetime.now())
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
        rating_text = RatingFormatter.format_daily_rating(stats)
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
        reply_markup=chat_actions_ikb(),
    )
