import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from container import container
from usecases.report.daily_rating import GetDailyTopUsersUseCase
from utils.exception_handler import handle_exception
from utils.rating_formatter import RatingFormatter
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(F.text == KbCommands.DAILY_RATING)
async def chat_daily_rating_handler(message: Message, state: FSMContext) -> None:
    """Обработчик для показа рейтинга выбранного чата за сутки."""
    try:
        # Получаем ID выбранного чата из состояния
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await message.answer(Dialog.Chat.CHAT_NOT_SELECTED)
            return

        # Получаем рейтинг за сегодня
        usecase: GetDailyTopUsersUseCase = container.resolve(GetDailyTopUsersUseCase)
        stats = await usecase.execute(chat_id=chat_id, date=datetime.now())

        # Форматируем рейтинг
        rating_text = RatingFormatter.format_daily_rating(stats)

        await send_html_message_with_kb(
            message=message,
            text=rating_text,
        )

        logger.info(
            f"Показан рейтинг для chat_id={chat_id} пользователю {message.from_user.username}"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении рейтинга чата: {e}", exc_info=True)
        await handle_exception(message, e, "chat_daily_rating_handler")
