from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.templates import templates_inline_kb
from services.templates import TemplateService
from states import TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.SELECT_TEMPLATE)
async def templates_list_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды для выбора области шаблонов.
    """
    from keyboards.inline.template_scope import template_scope_selection_kb
    from usecases.chat import GetTrackedChatsUseCase

    try:
        await state.clear()
        await state.set_state(TemplateStateManager.selecting_template_scope)

        # Получаем список чатов пользователя
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=str(message.from_user.id))

        await send_html_message_with_kb(
            message=message,
            text="Выберите область шаблонов:",
            reply_markup=template_scope_selection_kb(chats),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="templates_list_handler",
        )
