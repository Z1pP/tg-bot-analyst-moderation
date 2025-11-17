import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from keyboards.reply import admin_menu_kb, chat_actions_kb
from keyboards.reply.user_actions import user_actions_kb
from states import AllUsersReportStates, ChatStateManager, SingleUserReportStates
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.BACK)
async def back_to_menu_handler(message: Message, state: FSMContext) -> None:
    """Универсальный обработчик возврата в меню в зависимости от текущего state."""
    current_state = await state.get_state()
    logger.info("Возврат назад из state: %s", current_state)

    # Отчет по чату
    if current_state == ChatStateManager.selecting_period:
        data = await state.get_data()
        chat_id = data.get("chat_id")

        if not chat_id:
            await send_html_message_with_kb(
                message=message,
                text="Выберите чат заново",
                reply_markup=admin_menu_kb(),
            )
            await log_and_set_state(
                message=message,
                state=state,
                new_state=ChatStateManager.selecting_chat,
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=ChatStateManager.selecting_chat,
        )
        await send_html_message_with_kb(
            message=message,
            text="Возврат к меню чата.",
            reply_markup=chat_actions_kb(),
        )

    # Отчет по пользователю
    elif current_state == SingleUserReportStates.selecting_period:
        user_data = await state.get_data()
        user_id = user_data.get("user_id")

        if not user_id:
            await send_html_message_with_kb(
                message=message,
                text="Выберите пользователя заново",
                reply_markup=admin_menu_kb(),
            )
            return

        await log_and_set_state(
            message=message,
            state=state,
            new_state=SingleUserReportStates.selected_single_user,
        )
        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в меню",
            reply_markup=user_actions_kb(),
        )

    # Отчет по всем пользователям
    elif current_state == AllUsersReportStates.selecting_period:
        await log_and_set_state(
            message=message,
            state=state,
            new_state=AllUsersReportStates.selected_all_users,
        )
        await send_html_message_with_kb(
            message=message,
            text="Возвращаемся в меню",
            reply_markup=user_actions_kb(),
        )
