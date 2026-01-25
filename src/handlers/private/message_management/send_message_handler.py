import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.chat_dto import ChatDTO
from dto.message_action import SendMessageDTO
from exceptions.moderation import MessageSendError
from keyboards.inline.chats import select_chat_ikb
from keyboards.inline.message_actions import cancel_send_message_ikb, send_message_ikb
from states.message_management import MessageManagerState
from usecases.admin_actions import SendMessageToChatUseCase
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Messages.SEND_MESSAGE_TO_CHAT)
async def send_message_to_chat_handler(
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
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.NO_TRACKED_CHATS,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
        logger.warning(
            "Админ %s пытается отправить сообщение без отслеживаемых чатов",
            callback.from_user.username,
        )
        return

    # Сохраняем список чатов в state
    await state.update_data(
        user_chats=[chat.model_dump(mode="json") for chat in user_chats_dto.chats]
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.SELECT_CHAT,
        reply_markup=select_chat_ikb(user_chats_dto.chats),
    )
    await state.set_state(MessageManagerState.waiting_chat_select)
    logger.info("Админ %s выбирает чат для отправки сообщения", callback.from_user.id)


@router.callback_query(
    MessageManagerState.waiting_chat_select,
    F.data.startswith("select_chat_"),
)
async def chat_selected_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора чата для отправки сообщения."""
    await callback.answer()

    # Получаем chat_id из БД по id
    chat_id = int(callback.data.split("_")[2])

    # Получаем чат из UseCase чтобы взять chat_id (Telegram ID)
    data = await state.get_data()
    user_chats_data = data.get("user_chats")

    if not user_chats_data:
        logger.error("Отсутствуют данные о чатах в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.INVALID_STATE_DATA,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
        return

    user_chats = [ChatDTO.model_validate(chat) for chat in user_chats_data]

    # Находим выбранный чат
    selected_chat = next((chat for chat in user_chats if chat.id == chat_id), None)
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

    await state.update_data(chat_tgid=selected_chat.tg_id)

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
        selected_chat.tg_id,
    )


@router.message(MessageManagerState.waiting_content)
async def send_content_handler(
    message: types.Message, state: FSMContext, container: Container
) -> None:
    """Обработчик получения контента для отправки в чат."""
    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")

    if not chat_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await message.answer(
            Dialog.Messages.INVALID_STATE_DATA,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
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

        success_text = (
            f"{Dialog.Messages.SEND_SUCCESS}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}"
        )
        await message.answer(
            text=success_text,
            reply_markup=send_message_ikb(),
        )
        logger.info(
            "Админ %s отправил сообщение в чат %s",
            message.from_user.id,
            chat_tgid,
        )
    except MessageSendError as e:
        await message.answer(
            e.get_user_message(),
            reply_markup=send_message_ikb(),
        )
    except Exception as e:
        logger.error(
            "Ошибка отправки сообщения в чат %s: %s",
            chat_tgid,
            e,
            exc_info=True,
        )
        await message.answer(
            Dialog.Messages.REPLY_ERROR,
            reply_markup=send_message_ikb(),
        )

    await state.set_state(MessageManagerState.waiting_message_link)
