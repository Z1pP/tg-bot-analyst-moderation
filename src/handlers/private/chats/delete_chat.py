import logging
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import conf_remove_chat_kb, remove_inline_kb
from models import ChatSession
from repositories import ChatTrackingRepository
from services.user import UserService
from states import MenuStates
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(F.text == KbCommands.REMOVE_CHAT)  # TODO: Добавить state в роутер
async def delete_chat_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """Хендлер для команды удаления чата из отслеживания"""

    username = message.from_user.username

    logger.info(f"Получена команда удаления чата от {username}")

    try:
        user_service: UserService = container.resolve(UserService)
        user = await user_service.get_user(username=username)

        await state.update_data(user_id=user.id)

        # Получаем отслеживаемые чаты пользователя
        tracked_chats = await get_user_tracked_chats(user_id=user.id)

        if not tracked_chats:
            message_text = (
                "❌ У вас нет отслеживаемых чатов\n\n"
                "Сначала добавьте чаты в отслеживание."
            )

            await send_html_message_with_kb(
                message=message,
                text=message_text,
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
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        data = await state.get_data()
        chat_id = int(callback.data.split("__")[1])
        user_id = data.get("user_id", None)

        if not chat_id or not user_id:
            logger.error("Нет чат айди или юзер айди")

        await state.update_data(chat_id=chat_id)
        logger.info(f"Запрос подтверждения удаления чата из отслеживания: {chat_id}")

        message_text = "❗Вы уверены, что хотите удалить из отслеживаемых?"

        await send_html_message_with_kb(
            message=callback.message,
            text=message_text,
            reply_markup=conf_remove_chat_kb(),
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении чата из отслеживания:{e}")
        await callback.message.edit_text("Ошибка при отвязывании группы!")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("conf_remove_chat__"))
async def confirmation_removing_chat(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик подтверждения удаления чата из отслеживания"""
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id", None)
        user_id = data.get("user_id", None)
        answer = callback.data.split("__")[1]

        if answer == "yes":
            tracking_repository: ChatTrackingRepository = container.resolve(
                ChatTrackingRepository
            )

            success = await tracking_repository.remove_chat_from_tracking(
                admin_id=int(user_id),
                chat_id=chat_id,
            )

            if success:
                logger.info("Чат успешно удален из отслеживания")
                text = (
                    "✅ Готово! Чат удалён из отлеживания!\n\n"
                    "❗️Вы всегда можете вернуть чат в отслеживаемые "
                    "и продолжить собирать статистику"
                )
            else:
                logger.warning(f"Не удалось удалить чат {chat_id} из отслеживания")
                text = "❌ Чат не найден или уже удален."

            await callback.message.edit_text(text=text)
        else:
            logger.info(f"Удаление чата chat_id={chat_id} из отслеживания отменено")
            await callback.message.edit_text(
                text="❌ Удаление чата из отслеживания отменено!",
            )
    except Exception as e:
        await handle_exception(callback.message, e, "confirmation_removing_user")
    finally:
        await callback.answer()
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=MenuStates.chats_menu,
        )


async def get_user_tracked_chats(user_id: int) -> List[ChatSession]:
    """Получает список отслеживаемых чатов пользователя"""
    try:
        # Получаем сервисы
        tracking_repository: ChatTrackingRepository = container.resolve(
            ChatTrackingRepository
        )

        tracked_chats = await tracking_repository.get_all_tracked_chats(
            admin_id=user_id
        )

        logger.debug(
            f"Найдено {len(tracked_chats)} отслеживаемых чатов для user_id={user_id}"
        )

        return tracked_chats

    except Exception as e:
        logger.error(f"Ошибка при получении отслеживаемых чатов: {e}")
        raise
