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
    Обработчик команды для получения списка шаблонов сообщений.
    """

    try:
        await state.clear()  # Очистка состояния перед выводом списка чатов
        await state.set_state(TemplateStateManager.listing_templates)

        template_service: TemplateService = container.resolve(TemplateService)

        templates, total_count = await template_service.get_templates_with_count()

        message_text = (
            f"Найдено {total_count} шаблонов:" if total_count else "У вас нет шаблонов!"
        )

        await send_html_message_with_kb(
            message=message,
            text=message_text,
            reply_markup=templates_inline_kb(
                templates=templates,
                total_count=total_count,
            ),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="templates_list_handler",
        )
