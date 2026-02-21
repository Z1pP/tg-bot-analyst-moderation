import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CHATS_PAGE_SIZE
from dto.message_action import SendMessageDTO
from exceptions.moderation import MessageSendError
from keyboards.inline.chats import select_chat_ikb
from keyboards.inline.message_actions import (
    cancel_send_message_ikb,
    confirm_send_message_ikb,
    send_message_ikb,
)
from states.message_management import (
    ACTIVE_MESSAGE_ID,
    ADMIN_MESSAGE_ID,
    ADMIN_TGID,
    ADMIN_USERNAME,
    BROADCAST_ALL,
    CHAT_TGID,
    CHATNAME,
    MessageManagerState,
    get_send_confirm_state,
)
from dto.chat_dto import GetChatWithArchiveDTO
from usecases.admin_actions import (
    BroadcastMessageToTrackedChatsUseCase,
    SendMessageToChatUseCase,
)
from usecases.chat import GetChatWithArchiveUseCase
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from utils.send_message import safe_delete_message, safe_edit_message

from .helpers import show_message_management_menu

router = Router(name=__name__)
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
            "Администратор %s пытается отправить сообщение без отслеживаемых чатов",
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

    logger.info(
        "Администратор %s выбирает чат для отправки сообщения",
        callback.from_user.username,
    )

    chats = user_chats_dto.chats
    total_count = len(chats)
    first_page_chats = chats[:CHATS_PAGE_SIZE]

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.SELECT_CHAT,
        reply_markup=select_chat_ikb(
            chats=first_page_chats,
            page=1,
            total_count=total_count,
        ),
    )

    await state.set_state(MessageManagerState.waiting_select_chat)


@router.callback_query(
    MessageManagerState.waiting_select_chat,
    F.data.startswith(CallbackData.Messages.PREFIX_SELECT_CHAT),
)
async def process_select_chat_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора чата для отправки сообщения."""
    await callback.answer()

    suffix = callback.data.replace(CallbackData.Messages.PREFIX_SELECT_CHAT, "")

    if suffix == "all":
        # Рассылка во все чаты
        await state.update_data(
            {
                BROADCAST_ALL: True,
                CHAT_TGID: None,
                CHATNAME: "все отслеживаемые чаты",
                ACTIVE_MESSAGE_ID: callback.message.message_id,
            }
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.SEND_CONTENT_INPUT_ALL,
            reply_markup=cancel_send_message_ikb(),
        )

        logger.info(
            "Администратор %s выбрал рассылку во все чаты",
            callback.from_user.username,
        )
    else:
        # Выбор конкретного чата
        chat_id = int(suffix)

        get_chat_uc: GetChatWithArchiveUseCase = container.resolve(
            GetChatWithArchiveUseCase
        )
        selected_chat = await get_chat_uc.execute(
            GetChatWithArchiveDTO(chat_id=chat_id)
        )

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
            {
                BROADCAST_ALL: False,
                CHAT_TGID: selected_chat.chat_id,
                CHATNAME: selected_chat.title,
                ACTIVE_MESSAGE_ID: callback.message.message_id,
            }
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.SEND_CONTENT_INPUT.format(
                chat_title=selected_chat.title
            ),
            reply_markup=cancel_send_message_ikb(),
        )

        logger.info(
            "Администратор %s (id=%s) выбрал чат %s для отправки сообщения",
            callback.from_user.username,
            callback.from_user.id,
            selected_chat.chat_id,
        )

    await state.update_data({ACTIVE_MESSAGE_ID: callback.message.message_id})
    await state.set_state(MessageManagerState.waiting_content)


@router.message(MessageManagerState.waiting_content)
async def process_content_handler(
    message: types.Message,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик получения контента для отправки в чат. Сохраняет данные и показывает подтверждение."""
    data = await state.get_data()
    active_message_id = data.get(ACTIVE_MESSAGE_ID)
    broadcast_all = data.get(BROADCAST_ALL, False)
    chat_tgid = data.get(CHAT_TGID)
    chatname = data.get(CHATNAME, "")

    if not active_message_id:
        logger.error("Некорректные данные в state: %s", data)
        await message.answer(
            Dialog.Messages.INVALID_STATE_DATA,
            reply_markup=send_message_ikb(),
        )
        await state.clear()
        await safe_delete_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        return

    if not broadcast_all and not chat_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await show_message_management_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.INVALID_STATE_DATA,
        )
        await safe_delete_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        return

    admin_tgid = str(message.from_user.id)
    admin_username = message.from_user.username or "unknown"
    admin_message_id = message.message_id

    if broadcast_all:
        usecase_chats: GetUserTrackedChatsUseCase = container.resolve(
            GetUserTrackedChatsUseCase
        )
        user_chats_dto = await usecase_chats.execute(tg_id=admin_tgid)
        if not user_chats_dto.chats:
            await show_message_management_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=Dialog.Messages.NO_TRACKED_CHATS,
            )
            await safe_delete_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=message.message_id,
            )
            return

    await state.update_data(
        {
            ADMIN_TGID: admin_tgid,
            ADMIN_USERNAME: admin_username,
            ADMIN_MESSAGE_ID: admin_message_id,
        }
    )

    await safe_edit_message(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        text=Dialog.Messages.SEND_CONFIRM.format(chatname=chatname),
        reply_markup=confirm_send_message_ikb(),
    )
    await state.set_state(MessageManagerState.waiting_confirm_send)


@router.callback_query(
    MessageManagerState.waiting_confirm_send,
    F.data == CallbackData.Messages.CONFIRM_SEND_NO,
)
async def process_confirm_send_no_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик кнопки «Нет»: удаляет контент и показывает меню управления сообщениями."""
    await callback.answer()
    data = await state.get_data()
    active_message_id = data.get(ACTIVE_MESSAGE_ID)
    admin_message_id = data.get(ADMIN_MESSAGE_ID)
    await state.clear()
    if callback.bot and admin_message_id is not None:
        chat_id = (
            callback.message.chat.id if callback.message else callback.from_user.id
        )
        await safe_delete_message(
            bot=callback.bot,
            chat_id=chat_id,
            message_id=admin_message_id,
        )
    if callback.bot and callback.message and active_message_id is not None:
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
        )


@router.callback_query(
    MessageManagerState.waiting_confirm_send,
    F.data == CallbackData.Messages.CONFIRM_SEND_YES,
)
async def process_confirm_broadcast_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик подтверждения рассылки (отправки) сообщения в чаты (один чат)."""
    await callback.answer()

    confirm_state = await get_send_confirm_state(state)
    if not confirm_state:
        logger.error("Некорректные данные в state при подтверждении отправки")
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            state=state,
            text_prefix=Dialog.Messages.INVALID_STATE_DATA,
        )
        await state.clear()
        return

    chat_id = callback.message.chat.id
    active_message_id = confirm_state.active_message_id
    admin_message_id = confirm_state.admin_message_id

    try:
        if confirm_state.broadcast_all:
            usecase_broadcast: BroadcastMessageToTrackedChatsUseCase = (
                container.resolve(BroadcastMessageToTrackedChatsUseCase)
            )
            result = await usecase_broadcast.execute(
                admin_tgid=confirm_state.admin_tgid,
                admin_username=confirm_state.admin_username,
                admin_message_id=confirm_state.admin_message_id,
            )
            if result.success_count == 0 and result.failed_count == 0:
                text_prefix = Dialog.Messages.NO_TRACKED_CHATS
            elif result.failed_count == 0:
                text_prefix = Dialog.Messages.SEND_SUCCESS_ALL.format(
                    count=result.success_count
                )
            else:
                text_prefix = Dialog.Messages.SEND_PARTIAL_SUCCESS.format(
                    success_count=result.success_count,
                    failed_count=result.failed_count,
                )
            await show_message_management_menu(
                bot=callback.bot,
                chat_id=chat_id,
                message_id=active_message_id,
                state=state,
                text_prefix=text_prefix,
            )
            logger.info(
                "Админ %s разослал сообщение в %s чатов (%s с ошибками)",
                callback.from_user.id,
                result.success_count,
                result.failed_count,
            )
        else:
            if not confirm_state.chat_tgid:
                await show_message_management_menu(
                    bot=callback.bot,
                    chat_id=chat_id,
                    message_id=active_message_id,
                    state=state,
                    text_prefix=Dialog.Messages.INVALID_STATE_DATA,
                )
                await state.clear()
                return
            dto = SendMessageDTO(
                chat_tgid=confirm_state.chat_tgid,
                admin_tgid=confirm_state.admin_tgid,
                admin_username=confirm_state.admin_username,
                admin_message_id=confirm_state.admin_message_id,
            )
            try:
                usecase: SendMessageToChatUseCase = container.resolve(
                    SendMessageToChatUseCase
                )
                await usecase.execute(dto)
                await show_message_management_menu(
                    bot=callback.bot,
                    chat_id=chat_id,
                    message_id=active_message_id,
                    state=state,
                    text_prefix=Dialog.Messages.SEND_SUCCESS,
                )
                logger.info(
                    "Админ %s отправил сообщение в чат %s",
                    callback.from_user.id,
                    confirm_state.chat_tgid,
                )
            except MessageSendError as e:
                await show_message_management_menu(
                    bot=callback.bot,
                    chat_id=chat_id,
                    message_id=active_message_id,
                    state=state,
                    text_prefix=e.get_user_message(),
                )
            except Exception as e:
                logger.error(
                    "Ошибка отправки сообщения в чат %s: %s",
                    confirm_state.chat_tgid,
                    e,
                    exc_info=True,
                )
                await show_message_management_menu(
                    bot=callback.bot,
                    chat_id=chat_id,
                    message_id=active_message_id,
                    state=state,
                    text_prefix=Dialog.Messages.REPLY_ERROR,
                )
    finally:
        await state.clear()
        if callback.bot and admin_message_id is not None:
            await safe_delete_message(
                bot=callback.bot,
                chat_id=chat_id,
                message_id=admin_message_id,
            )
