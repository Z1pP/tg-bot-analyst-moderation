import logging
from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentActions as Actions
from keyboards.inline.banhammer import (
    no_reason_ikb,
    block_actions_ikb,
    back_to_block_menu_ikb,
)
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from services import UserService
from states import BanUserStates, BanHammerStates
from usecases.chat import GetChatsForUserActionUseCase
from usecases.moderation import GiveUserBanUseCase
from utils.state_logger import log_and_set_state
from utils.user_data_parser import parse_data_from_text
from container import container
from .common import process_moderation_action


router = Router()
logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(
    F.data == block_buttons.BLOCK_USER,
    BanHammerStates.block_menu,
)
async def block_user_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для блокировки пользователя.
    """
    await callback.answer()
    await state.update_data(message_to_edit_id=callback.message.message_id)

    await callback.message.edit_text(
        text=Dialog.BanUser.INPUT_USER_DATA,
        reply_markup=back_to_block_menu_ikb(),
    )
    await log_and_set_state(callback.message, state, BanUserStates.waiting_user_input)


@router.message(BanUserStates.waiting_user_input)
async def process_user_data_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """
    Обработчик для получения данных о пользователе.
    """
    user_data = parse_data_from_text(text=message.text)

    await message.delete()

    data = await state.get_data()
    message_to_edit_id = data.get("message_to_edit_id")

    if user_data is None:
        await bot.edit_message_text(
            text=Dialog.Error.INVALID_USERNAME_FORMAT,
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
        )
        return

    user_service: UserService = container.resolve(UserService)

    user = None

    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    if user is None:
        identificator = (
            f"<code>{user_data.tg_id}</code>"
            if user_data.tg_id
            else f"<b>@{user_data.username}</b>"
        )
        await bot.edit_message_text(
            text=Dialog.BanUser.USER_NOT_FOUND.format(
                identificator=identificator,
            ),
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
        )
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    if message_to_edit_id:
        try:
            await bot.edit_message_text(
                text=Dialog.BanUser.USER_INFO.format(
                    username=user.username,
                    tg_id=user.tg_id,
                ),
                chat_id=message.chat.id,
                message_id=message_to_edit_id,
                reply_markup=no_reason_ikb(),
            )
        except TelegramBadRequest as e:
            logger.error("Ошибка редактирования сообщения: %s", e, exc_info=True)

    await log_and_set_state(
        message=message,
        state=state,
        new_state=BanUserStates.waiting_reason_input,
    )


@router.message(BanUserStates.waiting_reason_input)
async def process_reason_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """
    Обработчик для получения причины блокировки.
    Удаляет сообщение пользователя с причиной и обновляет исходное сообщение.
    """
    reason = message.text.strip()

    await message.delete()

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")
    message_to_edit_id = data.get("message_to_edit_id")
    # ID чата берем из сообщения пользователя, т.к. это приватный чат с ботом
    chat_id = message.chat.id

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )
    chat_dtos = await usecase.execute(
        admin_tgid=str(message.from_user.id), user_tgid=user_tgid
    )

    # Если общих чатов для блокировки не найдено
    if not chat_dtos:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_to_edit_id,
            text=Dialog.BanUser.NO_CHATS.format(username=username),
            reply_markup=block_actions_ikb(),
        )
        await log_and_set_state(message, state, new_state=BanHammerStates.block_menu)
        return

    # Сохраняем причину и найденные чаты в состоянии
    await state.update_data(reason=reason, chat_dtos=chat_dtos)

    # Редактируем исходное сообщение, предлагая выбрать чат
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_to_edit_id,
        text=Dialog.BanUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_kb(dtos=chat_dtos),
    )
    await log_and_set_state(message, state, new_state=BanUserStates.waiting_chat_select)


@router.callback_query(
    BanUserStates.waiting_reason_input,
    F.data == block_buttons.NO_REASON,
)
async def process_no_reason(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для кнопки 'Без причины'."""
    await callback.answer()

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )

    chat_dtos = await usecase.execute(
        admin_tgid=str(callback.from_user.id),
        user_tgid=user_tgid,
    )

    if not chat_dtos:
        await callback.message.edit_text(
            text=Dialog.BanUser.NO_CHATS.format(username=username),
            reply_markup=block_actions_ikb(),
        )
        await log_and_set_state(callback.message, state, BanHammerStates.block_menu)
        return

    await state.update_data(reason=None, chat_dtos=chat_dtos)

    await callback.message.edit_text(
        text=Dialog.BanUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_kb(dtos=chat_dtos),
    )
    await log_and_set_state(callback.message, state, BanUserStates.waiting_chat_select)


@router.callback_query(
    BanUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def process_chat_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик для выбора чата для блокировки.
    """
    await process_moderation_action(
        callback=callback,
        state=state,
        action=Actions.BAN,
        usecase_cls=GiveUserBanUseCase,
        success_text="✅ Пользователь @{username} заблокирован!",
        partial_text=(
            "⚠️ Пользователь @{username} частично заблокирован\n\n"
            "✅ Успешно: {ok}\n❌ Ошибки: {fail}"
        ),
        fail_text="❌ Не удалось заблокировать @{username} ни в одном чате",
    )
