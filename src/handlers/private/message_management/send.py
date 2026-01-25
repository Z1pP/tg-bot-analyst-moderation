import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.message_action import SendMessageDTO
from exceptions.moderation import MessageSendError
from keyboards.inline.chats import select_chat_ikb
from keyboards.inline.message_actions import cancel_send_message_ikb, send_message_ikb
from services.chat.chat_service import ChatService
from states.message_management import MessageManagerState
from usecases.admin_actions import SendMessageToChatUseCase
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.send_message import safe_edit_message

from .ui import show_message_management_menu

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Messages.SEND_MESSAGE_TO_CHAT)
async def start_send_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик нажатия кнопки отправки сообщения."""
    await callback.answer()

    # Получаем отслеживаемые чаты
    usecase: GetUserTrackedChatsUseCase = container.resolve(GetUserTrackedChatsUseCase)
    user_chats_dto = await usecase.execute(tg_id=str(callback.from_user.id))

    if not user_chats_dto.chats:
        logger.info(
            "Админ %s пытается отправить сообщение без отслеживаемых чатов",
            callback.from_user.username,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.NO_TRACKED_CHATS,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
        return

    logger.info("Админ %s выбирает чат для отправки сообщения", callback.from_user.id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.SELECT_CHAT,
        reply_markup=select_chat_ikb(user_chats_dto.chats),
    )
    await state.update_data(active_message_id=callback.message.message_id)
    await state.set_state(MessageManagerState.waiting_chat_select)


@router.callback_query(
    MessageManagerState.waiting_chat_select,
    F.data.startswith(CallbackData.Messages.PREFIX_SELECT_CHAT),
)
async def select_chat_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора чата для отправки сообщения."""
    await callback.answer()

    # Получаем chat_id из БД по id
    chat_id = int(callback.data.replace(CallbackData.Messages.PREFIX_SELECT_CHAT, ""))

    chat_service: ChatService = container.resolve(ChatService)
    selected_chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not selected_chat:
        logger.error("Чат с id %s не найден", chat_id)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.INVALID_STATE_DATA,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
        return

    await state.update_data(
        chat_tgid=selected_chat.chat_id,
        active_message_id=callback.message.message_id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.SEND_CONTENT_INPUT,
        reply_markup=cancel_send_message_ikb(),
    )
    await state.set_state(MessageManagerState.waiting_content)
    logger.info(
        "Админ %s выбрал чат %s для отправки сообщения",
        callback.from_user.id,
        selected_chat.chat_id,
    )


@router.message(MessageManagerState.waiting_content)
async def process_content_handler(
    message: types.Message,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик получения контента для отправки в чат."""
    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    active_message_id = data.get("active_message_id")

    if not chat_tgid or not active_message_id:
        logger.error("Некорректные данные в state: %s", data)
        if active_message_id:
            await show_message_management_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=Dialog.Messages.INVALID_STATE_DATA,
            )
        else:
            await message.answer(
                Dialog.Messages.INVALID_STATE_DATA,
                reply_markup=send_message_ikb(),
            )
            await state.clear()

        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)
        return

    dto = SendMessageDTO(
        chat_tgid=chat_tgid,
        admin_tgid=str(message.from_user.id),
        admin_username=message.from_user.username or "unknown",
        admin_message_id=message.message_id,
    )

    try:
        usecase: SendMessageToChatUseCase = container.resolve(SendMessageToChatUseCase)
        await usecase.execute(dto)

        await show_message_management_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.SEND_SUCCESS,
        )
        logger.info(
            "Админ %s отправил сообщение в чат %s",
            message.from_user.id,
            chat_tgid,
        )
    except MessageSendError as e:
        await show_message_management_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=e.get_user_message(),
        )
    except Exception as e:
        logger.error(
            "Ошибка отправки сообщения в чат %s: %s",
            chat_tgid,
            e,
            exc_info=True,
        )
        await show_message_management_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.REPLY_ERROR,
        )
    finally:
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)
