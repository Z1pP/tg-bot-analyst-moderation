import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog, KbCommands
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import conf_remove_chat_kb, remove_inline_kb
from states import MenuStates
from usecases.chat_tracking import (
    GetUserTrackedChatsUseCase,
    RemoveChatFromTrackingUseCase,
)
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
        # Получаем отслеживаемые чаты пользователя
        usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        tg_id = str(message.from_user.id)
        user_chats_dto = await usecase.execute(tg_id=tg_id)

        await state.update_data(user_id=user_chats_dto.user_id)

        if not user_chats_dto.chats:
            message_text = Dialog.Chat.NO_TRACKED_CHATS

            await send_html_message_with_kb(
                message=message,
                text=message_text,
            )
            return

        message_text = Dialog.Chat.REMOVE_CHAT_TITLE

        # Показываем первую страницу
        first_page_chats = user_chats_dto.chats[:CHATS_PAGE_SIZE]

        await send_html_message_with_kb(
            message=message,
            text=message_text,
            reply_markup=remove_inline_kb(
                chats=first_page_chats,
                page=1,
                total_count=user_chats_dto.total_count,
            ),
        )

        logger.info(
            f"Показан список из {user_chats_dto.total_count} отслеживаемых чатов "
            "для {message.from_user.username}"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}", exc_info=True)
        await message.answer(Dialog.Chat.ERROR_GET_CHATS)


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

        message_text = Dialog.Chat.CONFIRM_REMOVE_CHAT

        await send_html_message_with_kb(
            message=callback.message,
            text=message_text,
            reply_markup=conf_remove_chat_kb(),
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении чата из отслеживания:{e}")
        await callback.message.edit_text(Dialog.Chat.ERROR_UNTRACK_CHAT)
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
            usecase: RemoveChatFromTrackingUseCase = container.resolve(
                RemoveChatFromTrackingUseCase
            )

            success, error_msg = await usecase.execute(
                user_id=int(user_id), chat_id=chat_id
            )

            if success:
                text = Dialog.Chat.CHAT_REMOVED
            else:
                text = Dialog.Chat.ERROR_REMOVE_CHAT.format(
                    error_msg=error_msg or "Чат не найден или уже удален"
                )

            await callback.message.edit_text(text=text)
        else:
            logger.info(f"Удаление чата chat_id={chat_id} из отслеживания отменено")
            await callback.message.edit_text(
                text=Dialog.Chat.REMOVE_CANCELLED,
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
