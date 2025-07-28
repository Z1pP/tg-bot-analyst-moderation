import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import remove_inline_kb
from keyboards.reply.menu import get_back_kb
from repositories import ChatTrackingRepository
from services.user import UserService
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(F.text == KbCommands.REMOVE_CHAT)
async def delete_chat_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """Хендлер для команды удаления чата из отслеживания"""

    logger.info(f"Получена команда удаления чата от {message.from_user.username}")

    try:
        # Получаем отслеживаемые чаты пользователя
        tracked_chats = await get_user_tracked_chats(
            username=message.from_user.username
        )

        if not tracked_chats:
            message_text = (
                "📋 <b>Удаление чата из отслеживания</b>\n\n"
                "❌ У вас нет отслеживаемых чатов\n\n"
                "Сначала добавьте чаты в отслеживание."
            )

            await send_html_message_with_kb(
                message=message,
                text=message_text,
                reply_markup=get_back_kb(),
            )
            return

        message_text = (
            "📋 <b>Удаление чата из отслеживания</b>\n\n"
            "Выберите способ удаления:\n\n"
            "🔹 <b>Способ 1:</b> Выберите чат из списка ниже\n"
            "🔹 <b>Способ 2:</b> Выполните команду <code>/untrack</code> в нужном чате\n\n"
            "📋 <b>Ваши отслеживаемые чаты:</b>"
        )

        await send_html_message_with_kb(
            message=message,
            text=message_text,
            reply_markup=remove_inline_kb(tracked_chats),
        )

        logger.info(
            f"Показан список из {len(tracked_chats)} отслеживаемых чатов "
            "для {message.from_user.username}"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при получении списка чатов")


@router.callback_query(F.data.startswith("untrack_chat__"))
async def process_untracking_chat(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    pass


async def get_user_tracked_chats(username: str) -> list:
    """Получает список отслеживаемых чатов пользователя"""
    try:
        # Получаем сервисы
        tracking_repository: ChatTrackingRepository = container.resolve(
            ChatTrackingRepository
        )
        user_service: UserService = container.resolve(UserService)

        user = await user_service.get_user(username=username)

        tracked_chats = await tracking_repository.get_all_tracked_chats(
            admin_id=user.id
        )

        logger.debug(f"Найдено {len(tracked_chats)} отслеживаемых чатов для {username}")

        return tracked_chats

    except Exception as e:
        logger.error(f"Ошибка при получении отслеживаемых чатов: {e}")
        return []
