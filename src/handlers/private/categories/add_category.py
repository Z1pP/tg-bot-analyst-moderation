from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.reply.menu import tamplates_menu_kb
from usecases.categories import CreateCategoryUseCase
from states import TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.ADD_CATEGORY)
async def add_category_handler(message: Message, state: FSMContext):
    """Обработчик добавления категории"""

    text = "Введите название категории:"

    await send_html_message_with_kb(
        message=message,
        text=text,
    )
    await state.set_state(TemplateStateManager.process_category_name)


@router.message(TemplateStateManager.process_category_name)
async def process_category_name_handler(message: Message, state: FSMContext):
    """Обработчик названия категории"""

    usecase: CreateCategoryUseCase = container.resolve(CreateCategoryUseCase)

    try:
        category = await usecase.execute(name=message.text)

        text = f'🧩 Успешно создана новая категория - <b>"{category.name}"</b>'

        await send_html_message_with_kb(
            message=message,
            text=text,
            reply_markup=tamplates_menu_kb(),
        )

        await state.set_state(TemplateStateManager.templates_menu)
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="process_category_name_handler",
        )



