import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import tracked_chats_inline_kb
from states.chat_states import ChatStateManager
from usecases.chat import GetAllChatsUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(F.text == KbCommands.TRACKED_CHATS)
async def list_of_tracking_chats_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка трекающих чатов.
    """
    try:
        # Устанавливаем состояние вывода списка трекающих чатов
        await state.set_state(ChatStateManager.listing_tracking_chats)

        username = message.from_user.username

        usecase: GetAllChatsUseCase = container.resolve(GetAllChatsUseCase)
        chats = await usecase.execute(username)

        text = (
            "Получатель - чат, куда будут приходить отчеты\n"
            "Источник - чат, в котором бот собирает информацию\n"
            "✅ - указывает на то, что в данный момент делает чат.\n"
        )

        # Отправляем сообщение с кнопками для выбора действия
        await send_html_message_with_kb(
            message=message,
            text=text,
            reply_markup=tracked_chats_inline_kb(chats=chats),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="list_of_tracking_chats_handler",
        )
