import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.chats_kb import tracked_chats_inline_kb
from states.chat_states import ChatStateManager
from usecases.chat import GetTrackedChatsUseCase
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

        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(username)

        text = (
            "<b>Управление отслеживаемыми чатами</b>\n\n"
            "• <b>✅ Получатель</b> - чат, куда будут отправляться отчеты\n"
            "• <b>✅ Источник</b> - чат, из которого бот собирает статистику\n\n"
            "Нажмите на кнопку, чтобы изменить статус чата:\n"
            "• <b>❌ Получатель</b> → <b>✅ Получатель</b>: включить отправку отчетов в этот чат\n"
            "• <b>✅ Получатель</b> → <b>❌ Получатель</b>: отключить отправку отчетов в этот чат\n"
            "• <b>❌ Источник</b> → <b>✅ Источник</b>: начать сбор статистики из этого чата\n"
            "• <b>✅ Источник</b> → <b>❌ Источник</b>: прекратить сбор статистики из этого чата\n\n"
            "<i>Примечание: чат не может одновременно быть и источником, и получателем.</i>"
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
