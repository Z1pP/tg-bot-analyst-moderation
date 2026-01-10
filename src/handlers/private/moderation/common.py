import logging
from typing import Optional, Type, Union

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from punq import Container

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from dto.chat_dto import ChatDTO
from keyboards.inline.banhammer import back_to_block_menu_ikb, moderation_menu_ikb
from keyboards.inline.chats import tracked_chats_with_all_ikb
from services import UserService
from states.moderation import ModerationStates
from usecases.chat import GetChatsForUserActionUseCase
from usecases.moderation import GiveUserBanUseCase, GiveUserWarnUseCase
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

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

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=dialog_text,
        reply_markup=back_to_block_menu_ikb(),
    )
    await state.set_state(next_state)


async def process_moderation_action(
    callback: types.CallbackQuery,
    state: FSMContext,
    action: Actions,
    usecase_cls: Type[ModerationUsecase],
    success_text: str,
    partial_text: str,
    fail_text: str,
    container: Container,
) -> None:
    """Общая логика для выдачи бана/предупреждения пользователю"""

    data = await state.get_data()
    chat_id_from_callback = callback.data.split("__")[1]
    chat_dtos_data = data.get("chat_dtos")
    username = data.get("username")
    user_tgid = data.get("tg_id")

    if not chat_dtos_data or not username or not user_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Ошибка: некорректные данные. Попробуйте снова.",
            reply_markup=moderation_menu_ikb(),
        )
        return

    chat_dtos = [ChatDTO.model_validate(chat) for chat in chat_dtos_data]

    if chat_id_from_callback != "all":
        chat_dtos = [
            chat for chat in chat_dtos if chat.id == int(chat_id_from_callback)
        ]

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

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=response_text,
        reply_markup=moderation_menu_ikb(),
    )

    await state.set_state(ModerationStates.menu)


async def process_user_input_common(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
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
            kwargs["reply_markup"] = moderation_menu_ikb()

        await safe_edit_message(bot=bot, **kwargs)

        if error_state:
            await state.set_state(error_state)
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
            kwargs["reply_markup"] = moderation_menu_ikb()

        await safe_edit_message(bot=bot, **kwargs)

        if error_state:
            await state.set_state(error_state)
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    if message_to_edit_id:
        await safe_edit_message(
            bot=bot,
            text=dialog_texts["user_info"].format(
                username=user.username,
                tg_id=user.tg_id,
            ),
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
            reply_markup=success_keyboard(),
        )

    await state.set_state(next_state)


async def process_reason_common(
    reason: Optional[str],
    sender: types.Message | types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
    container: Container,
    is_callback: bool,
    next_state: State,
) -> None:
    """
    Общая логика для получения причины предупреждения.
    Работает и для сообщений, и для callback-запросов.
    """
    chat_id = sender.message.chat.id if is_callback else sender.chat.id
    from_user_id = sender.from_user.id
    message_to_edit_id = None

    if not is_callback:
        await sender.delete()

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")
    message_to_edit_id = data.get("message_to_edit_id")

    logger.info(
        "admin_id=%s, user_tgid=%s, username=%s, reason=%s",
        from_user_id,
        user_tgid,
        username,
        "<none>" if reason is None else reason,
    )

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )
    chat_dtos = await usecase.execute(admin_tgid=str(from_user_id), user_tgid=user_tgid)

    if not chat_dtos:
        await safe_edit_message(
            bot=bot,
            chat_id=chat_id,
            message_id=message_to_edit_id,
            text=Dialog.WarnUser.NO_CHATS.format(username=username),
            reply_markup=moderation_menu_ikb(),
        )
        await state.set_state(ModerationStates.menu)
        logger.warning(
            "Отслеживаемы чаты не найдены для пользователя %s (%s)",
            username,
            user_tgid,
        )
        return

    await state.update_data(
        reason=reason,
        chat_dtos=[chat.model_dump(mode="json") for chat in chat_dtos],
    )

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_to_edit_id,
        text=Dialog.WarnUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_ikb(dtos=chat_dtos),
    )

    await state.set_state(next_state)
