import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from typing import Union

from constants import InlineButtons
from container import container
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from keyboards.inline.banhammer import block_actions_ikb
from states.banhammer_states import BanHammerStates
from usecases.moderation import GiveUserWarnUseCase, GiveUserBanUseCase
from utils.state_logger import log_and_set_state

ModerationUsecase = Union[GiveUserWarnUseCase, GiveUserBanUseCase]

logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


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
