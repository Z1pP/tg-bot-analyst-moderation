import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from container import container
from keyboards.inline.chats_kb import (
    chats_management_ikb,
    conf_remove_chat_ikb,
    remove_chat_ikb,
)
from states import MenuStates
from usecases.chat_tracking import (
    GetUserTrackedChatsUseCase,
    RemoveChatFromTrackingUseCase,
)
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.REMOVE)
async def delete_chat_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Хендлер для команды удаления чата из отслеживания через callback"""
    await callback.answer()

    tg_id = str(callback.from_user.id)

    logger.info(
        "Пользователь %s начал удаление чата из отслеживания",
        callback.from_user.username,
    )

    try:
        usecase: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await usecase.execute(tg_id=tg_id)
    except Exception as e:
        logger.error("Ошибка при получении списка чатов: %s", e, exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHATS,
            reply_markup=chats_management_ikb(),
        )
        return

    await state.update_data(user_id=user_chats_dto.user_id)

    if not user_chats_dto.chats:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.NO_TRACKED_CHATS,
            reply_markup=chats_management_ikb(),
        )
        return

    message_text = Dialog.Chat.REMOVE_CHAT_TITLE
    first_page_chats = user_chats_dto.chats[:CHATS_PAGE_SIZE]

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=message_text,
        reply_markup=remove_chat_ikb(
            chats=first_page_chats,
            page=1,
            total_count=user_chats_dto.total_count,
        ),
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

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_UNTRACK_CHAT, ""))

    logger.info(
        "Пользователь %s начал удаление чата из отслеживания: %s",
        callback.from_user.username,
        chat_id,
    )

    await state.update_data(chat_id=chat_id)

    message_text = Dialog.Chat.CONFIRM_REMOVE_CHAT

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=message_text,
        reply_markup=conf_remove_chat_ikb(),
    )


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT),
)
async def confirmation_removing_chat_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик подтверждения удаления чата из отслеживания"""
    await callback.answer()

    answer = callback.data.replace(CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT, "")

    data = await state.get_data()
    chat_id = data.get("chat_id", None)
    user_id = data.get("user_id", None)

    if answer == "yes":
        logger.info(
            "Пользователь %s подтвердил удаление чата из отслеживания: %s",
            callback.from_user.username,
            answer,
        )

        try:
            usecase: RemoveChatFromTrackingUseCase = container.resolve(
                RemoveChatFromTrackingUseCase
            )

            success, error_msg = await usecase.execute(
                user_id=int(user_id), chat_id=chat_id
            )
        except Exception as e:
            logger.error(
                "Ошибка при удалении чата из отслеживания: %s", e, exc_info=True
            )
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Chat.ERROR_REMOVE_CHAT,
                reply_markup=chats_management_ikb(),
            )
            return

        if success:
            text = Dialog.Chat.CHAT_REMOVED
        else:
            text = Dialog.Chat.ERROR_REMOVE_CHAT.format(
                error_msg=error_msg or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
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

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=chats_management_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.chats_menu,
    )
