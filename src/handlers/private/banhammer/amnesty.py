import logging
from dataclasses import dataclass

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import KbCommands
from container import container
from exceptions.moderation import ModerationError
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from services import BotMessageService
from states import AmnestyStates, BanHammerStates
from usecases.amnesty import GetChatsWithBannedUserUseCase, UnbanUserUseCase
from utils.state_logger import log_and_set_state

from ..users.add_user_to_tracking import parse_data_from_text

router = Router()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UserData:
    tg_username: str
    tg_id: str


@router.message(
    F.text == KbCommands.AMNESTY,
    BanHammerStates.block_menu,
)
async def amnesty_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик отвечающий за разблокировку пользователей в чате.
    """
    text = (
        "Чтобы разблокировать юзера, пожалуйста, пришлите:\n • @тег_юзера\n • ID юзера"
    )
    await message.reply(text=text)
    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_user_input,
    )


@router.message(
    AmnestyStates.waiting_user_input,
)
async def waiting_user_data_input(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для обработки введенной информации о пользователе
    """
    parse_data = parse_data_from_text(text=message.text)

    await state.update_data(
        tg_username=parse_data.username,
        tg_id=parse_data.user_tgid,
    )

    usecase: GetChatsWithBannedUserUseCase = container.resolve(
        GetChatsWithBannedUserUseCase
    )
    chat_dtos = await usecase.execute(
        admin_tgid=str(message.from_user.id),
        violator_tgid=parse_data.user_tgid,
    )

    if not chat_dtos:
        text = "❗Нет чатов, где этот пользователь забанен."
        await message.reply(text=text)
        return

    text = f"Выберите чат, в котором провести амнистию юзера @{parse_data.username}"

    await message.reply(
        text=text,
        reply_markup=tracked_chats_with_all_kb(
            dtos=chat_dtos,
            total_count=len(chat_dtos),
        ),
    )
    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_chat_select,
    )


@router.callback_query(
    AmnestyStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def waiting_chat_select(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для обработки выбора чата
    """
    await callback.answer()

    try:
        data = await state.get_data()
        violator_tgid = data.get("tg_id")
        violator_username = data.get("tg_username")

        chat_id_str = callback.data.split("__")[1]

        usecase: UnbanUserUseCase = container.resolve(UnbanUserUseCase)

        if chat_id_str == "all":
            unbanned_chats = await usecase.execute(
                admin_tgid=str(callback.from_user.id),
                violator_tgid=violator_tgid,
            )
            chats_list = ", ".join(unbanned_chats)
            text = f"✅ Пользователь @{violator_username} разблокирован в чатах <b>{chats_list}</b>!"
        else:
            chat_id = int(chat_id_str)
            unbanned_chats = await usecase.execute(
                admin_tgid=str(callback.from_user.id),
                violator_tgid=violator_tgid,
                chat_ids=[chat_id],
            )
            if unbanned_chats:
                text = f"✅ Пользователь @{violator_username} разблокирован в чате <b>{unbanned_chats[0]}</b>!"
            else:
                text = "❌ Не удалось разблокировать пользователя."

        await callback.message.edit_text(text=text)
        await state.clear()

    except ModerationError as e:
        bot_message_service: BotMessageService = container.resolve(BotMessageService)
        await bot_message_service.send_private_message(
            user_tgid=callback.from_user.id,
            text=e.get_user_message(),
        )
        await state.clear()
