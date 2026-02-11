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

    suffix = callback.data.replace(CallbackData.Messages.PREFIX_SELECT_CHAT, "")

    if suffix == "all":
        # Рассылка во все чаты
        await state.update_data(
            broadcast_all=True,
            chat_tgid=None,
            active_message_id=callback.message.message_id,
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
            broadcast_all=False,
            chat_tgid=selected_chat.chat_id,
            active_message_id=callback.message.message_id,
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
            "Администратор %s выбрал чат %s для отправки сообщения",
            callback.from_user.username,
            callback.from_user.id,
            selected_chat.chat_id,
        )

    await state.set_state(MessageManagerState.waiting_content)


@router.message(MessageManagerState.waiting_content)
async def process_content_handler(
    message: types.Message,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик получения контента для отправки в чат."""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    broadcast_all = data.get("broadcast_all", False)
    chat_tgid = data.get("chat_tgid")

    if not active_message_id:
        logger.error("Некорректные данные в state: %s", data)
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

    if not broadcast_all and not chat_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await show_message_management_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.INVALID_STATE_DATA,
        )
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)
        return

    admin_tgid = str(message.from_user.id)
    admin_username = message.from_user.username or "unknown"
    admin_message_id = message.message_id

    try:
        if broadcast_all:
            # Рассылка во все чаты
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
                try:
                    await message.delete()
                except Exception as e:
                    logger.warning("Не удалось удалить сообщение пользователя: %s", e)
                return

            usecase_send: SendMessageToChatUseCase = container.resolve(
                SendMessageToChatUseCase
            )
            success_count = 0
            failed_count = 0

            for chat in user_chats_dto.chats:
                dto = SendMessageDTO(
                    chat_tgid=chat.tg_id,
                    admin_tgid=admin_tgid,
                    admin_username=admin_username,
                    admin_message_id=admin_message_id,
                )
                try:
                    await usecase_send.execute(dto)
                    success_count += 1
                except MessageSendError as e:
                    logger.warning(
                        "Не удалось отправить сообщение в чат %s: %s",
                        chat.tg_id,
                        e,
                    )
                    failed_count += 1
                except Exception as e:
                    logger.error(
                        "Ошибка отправки сообщения в чат %s: %s",
                        chat.tg_id,
                        e,
                        exc_info=True,
                    )
                    failed_count += 1

            if failed_count == 0:
                text_prefix = Dialog.Messages.SEND_SUCCESS_ALL.format(
                    count=success_count
                )
            else:
                text_prefix = Dialog.Messages.SEND_PARTIAL_SUCCESS.format(
                    success_count=success_count,
                    failed_count=failed_count,
                )

            await show_message_management_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=text_prefix,
            )
            logger.info(
                "Админ %s разослал сообщение в %s чатов (%s с ошибками)",
                message.from_user.id,
                success_count,
                failed_count,
            )
        else:
            # Отправка в один чат
            dto = SendMessageDTO(
                chat_tgid=chat_tgid,
                admin_tgid=admin_tgid,
                admin_username=admin_username,
                admin_message_id=admin_message_id,
            )

            try:
                usecase: SendMessageToChatUseCase = container.resolve(
                    SendMessageToChatUseCase
                )
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
