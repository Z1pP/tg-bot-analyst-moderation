import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    back_to_chats_menu_ikb,
    chats_menu_ikb,
    conf_remove_chat_ikb,
)
from usecases.chat_tracking import (
    RemoveChatFromTrackingUseCase,
)
from utils.send_message import safe_edit_callback_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.REMOVE)
async def untrack_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Хендлер для команды удаления чата из отслеживания через callback"""
    await callback.answer()

    logger.info(
        "Администратор tg_id: %d username: %s начал удаление чата из отслеживания",
        callback.from_user.id,
        callback.from_user.username,
    )

    message_text = Dialog.Chat.UNTRACK_CHAT_INFO

    await safe_edit_callback_message(
        callback=callback,
        text=message_text,
        reply_markup=back_to_chats_menu_ikb(),
    )


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_UNTRACK_CHAT),
)
async def process_untracking_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для получения ID выбранного чата на удаление."""
    await callback.answer()
    if callback.data is None:
        return

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_UNTRACK_CHAT, ""))

    logger.info(
        "Пользователь %s начал удаление чата из отслеживания: %s",
        callback.from_user.username,
        chat_id,
    )

    await state.update_data(chat_id=chat_id)

    message_text = Dialog.Chat.CONFIRM_REMOVE_CHAT

    await safe_edit_callback_message(
        callback=callback,
        text=message_text,
        reply_markup=conf_remove_chat_ikb(),
    )


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT),
)
async def confirmation_untracking_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик подтверждения удаления чата из отслеживания"""
    await callback.answer()
    if callback.data is None:
        return

    answer = callback.data.replace(CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT, "")

    data = await state.get_data()
    chat_id = data.get("chat_id", None)

    if answer == "yes":
        logger.info(
            "Пользователь %s подтвердил удаление чата из отслеживания: %s",
            callback.from_user.username,
            answer,
        )

        if not isinstance(chat_id, int):
            text = Dialog.Chat.ERROR_REMOVE_CHAT.format(
                error_msg=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
        else:
            try:
                usecase: RemoveChatFromTrackingUseCase = container.resolve(
                    RemoveChatFromTrackingUseCase
                )
                result = await usecase.execute(
                    admin_tg_id=str(callback.from_user.id),
                    admin_username=callback.from_user.username,
                    chat_id=chat_id,
                )
                if result.success:
                    text = Dialog.Chat.CHAT_REMOVED
                else:
                    text = Dialog.Chat.ERROR_REMOVE_CHAT.format(
                        error_msg=result.error_message
                        or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
                    )
            except Exception as e:
                logger.error(
                    "Ошибка при удалении чата из отслеживания: %s", e, exc_info=True
                )
                await safe_edit_callback_message(
                    callback=callback,
                    text=Dialog.Chat.ERROR_REMOVE_CHAT,
                    reply_markup=chats_menu_ikb(),
                )
                return
    elif answer == "no":
        logger.info(
            "Пользователь %s отменил удаление чата из отслеживания: %s",
            callback.from_user.username,
            chat_id,
        )
        text = Dialog.Chat.REMOVE_CANCELLED
    else:
        logger.warning(
            "Пользователь %s отправил неверный ответ на подтверждение удаления чата: %s",
            callback.from_user.username,
            answer,
        )
        text = Dialog.Chat.ANSWER_NOT_VALID

    await safe_edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=chats_menu_ikb(),
    )
