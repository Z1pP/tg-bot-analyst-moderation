import logging
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State


from typing import Optional, Union

from constants import InlineButtons
from container import container
from services import UserService
from utils.user_data_parser import parse_data_from_text
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from keyboards.inline.banhammer import back_to_block_menu_ikb, block_actions_ikb
from states.banhammer_states import BanHammerStates
from usecases.moderation import GiveUserWarnUseCase, GiveUserBanUseCase
from utils.state_logger import log_and_set_state

ModerationUsecase = Union[GiveUserWarnUseCase, GiveUserBanUseCase]

logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


async def process_user_handler_common(
    callback: types.CallbackQuery,
    state: FSMContext,
    *,
    next_state: State,
    dialog_text: str,
) -> None:
    """Общая логика для обработчиков пользователя (warn / block / amnesty)"""
    await callback.answer()
    await state.update_data(message_to_edit_id=callback.message.message_id)

    await callback.message.edit_text(
        text=dialog_text,
        reply_markup=back_to_block_menu_ikb(),
    )
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=next_state,
    )


async def process_moderation_action(
    callback: types.CallbackQuery,
    state: FSMContext,
    action: Actions,
    usecase_cls: ModerationUsecase,
    success_text: str,
    partial_text: str,
    fail_text: str,
) -> None:
    pass
    """Общая логика для выдачи бана/предупреждения пользователю"""

    data = await state.get_data()
    chat_id = callback.data.split("__")[1]
    chat_dtos = data.get("chat_dtos")
    username = data.get("username")
    user_tgid = data.get("tg_id")

    if not chat_dtos or not username or not user_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await callback.message.edit_text(
            text="❌ Ошибка: некорректные данные. Попробуйте снова.",
            reply_markup=block_actions_ikb(),
        )
        return

    if chat_id != "all":
        chat_dtos = [chat for chat in chat_dtos if chat.id == int(chat_id)]

    logger.info(
        "Начало действия %s пользователя %s в %s чатах",
        action.value,
        username,
        len(chat_dtos),
    )

    usecase = container.resolve(usecase_cls)

    success_chats = []
    failed_chats = []

    for chat in chat_dtos:
        dto = ModerationActionDTO(
            action=action,
            violator_tgid=user_tgid,
            violator_username=username,
            admin_tgid=str(callback.from_user.id),
            admin_username=callback.from_user.username,
            chat_tgid=chat.tg_id,
            chat_title=chat.title,
            reason=data.get("reason"),
            from_admin_panel=True,
        )

        try:
            await usecase.execute(dto=dto)
            success_chats.append(chat.title)
            logger.info("Действие %s в чате %s успешно", action.value, chat.title)
        except Exception as e:
            failed_chats.append(chat.title)
            logger.error(
                "Ошибка действия %s в чате %s: %s",
                action.value,
                chat.title,
                e,
                exc_info=True,
            )

    # Формирование ответа
    if success_chats and not failed_chats:
        response_text = success_text.format(username=username)
        if len(success_chats) > 1:
            response_text += (
                f"\n\nЧаты ({len(success_chats)}): {', '.join(success_chats)}"
            )
    elif success_chats and failed_chats:
        response_text = partial_text.format(
            username=username,
            ok=", ".join(success_chats),
            fail=", ".join(failed_chats),
        )
    else:
        response_text = fail_text.format(username=username)

    await callback.message.edit_text(
        text=response_text,
        reply_markup=block_actions_ikb(),
    )

    await log_and_set_state(callback.message, state, BanHammerStates.block_menu)


async def process_user_input_common(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    *,
    dialog_texts: dict[str, str],
    success_keyboard: types.InlineKeyboardMarkup,
    next_state: State,
    error_state: Optional[State] = None,
    show_block_actions_on_error: bool = False,
):
    """
    Общая логика для хендлеров получения данных пользователя (ban / warn / amnesty).
    """
    user_data = parse_data_from_text(text=message.text)
    await message.delete()

    data = await state.get_data()
    message_to_edit_id = data.get("message_to_edit_id")

    if user_data is None:
        kwargs = dict(
            text=dialog_texts["invalid_format"],
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
        )
        if show_block_actions_on_error:
            kwargs["reply_markup"] = block_actions_ikb()

        await bot.edit_message_text(**kwargs)

        if error_state:
            await log_and_set_state(message=message, state=state, new_state=error_state)
        return

    user_service: UserService = container.resolve(UserService)

    user = None
    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    # --- Если пользователь не найден
    if user is None:
        identificator = (
            f"<code>{user_data.tg_id}</code>"
            if user_data.tg_id
            else f"<b>@{user_data.username}</b>"
        )
        kwargs = dict(
            text=dialog_texts["user_not_found"].format(identificator=identificator),
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
        )
        if show_block_actions_on_error:
            kwargs["reply_markup"] = block_actions_ikb()

        await bot.edit_message_text(**kwargs)

        if error_state:
            await log_and_set_state(message=message, state=state, new_state=error_state)
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    if message_to_edit_id:
        try:
            await bot.edit_message_text(
                text=dialog_texts["user_info"].format(
                    username=user.username,
                    tg_id=user.tg_id,
                ),
                chat_id=message.chat.id,
                message_id=message_to_edit_id,
                reply_markup=success_keyboard(),
            )
        except TelegramBadRequest as e:
            logger.error("Ошибка редактирования сообщения: %s", e, exc_info=True)

    await log_and_set_state(
        message=message,
        state=state,
        new_state=next_state,
    )
