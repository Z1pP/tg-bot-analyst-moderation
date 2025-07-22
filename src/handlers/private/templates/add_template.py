import logging
from typing import Any, Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.categories import categories_inline_kb
from middlewares import AlbumMiddleware
from services.answers_templates import TemplateContentService
from services.categories import CategoryService
from states import TemplateStateManager
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)
router.message.middleware(AlbumMiddleware())
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.ADD_TEMPLATE)
async def add_template_handler(message: Message, state: FSMContext):
    """Обработчик добавления нового шаблона"""
    try:
        # Получаем сервис и категории
        category_service: CategoryService = container.resolve(CategoryService)
        categories = await category_service.get_categories()

        # Устанавливаем состояние для выбора категории
        await state.set_state(TemplateStateManager.process_template_category)

        await send_html_message_with_kb(
            message=message,
            text="Пожалуйста, выберите категорию шаблона:",
            reply_markup=categories_inline_kb(categories=categories),
        )

    except Exception as e:
        logger.error(f"Ошибка при начале создания шаблона: {e}")
        await message.answer("Произошла ошибка при создании шаблона.")
        await state.clear()


@router.message(TemplateStateManager.process_template_title)
async def process_template_title_handler(message: Message, state: FSMContext):
    """Обработчик получения названия нового шаблона"""
    try:
        await state.update_data(title=message.text)

        # Устанавливаем состояние для ввода контента для шаблона
        await state.set_state(TemplateStateManager.process_template_content)

        await send_html_message_with_kb(
            message=message,
            text=f"Отправьте контент для шаблона '{message.text}' (текст, фото или медиагруппу):",
        )
    except Exception as e:
        logger.error(f"Ошибка при получении названия шаблона: {e}")
        await message.answer("Произошла ошибка при создании шаблона.")
        await state.clear()


@router.message(TemplateStateManager.process_template_content)
async def process_template_content_handler(
    message: Message,
    state: FSMContext,
    album_messages: list[Message] | None = None,
):
    """Обработчик получения контента шаблона"""
    state_data = await state.get_data()
    title = state_data.get("title")

    try:
        # Устанавлием состояния меню шаблонов
        await state.set_state(TemplateStateManager.templates_menu)

        # Получаем сервисы
        content_service: TemplateContentService = container.resolve(
            TemplateContentService
        )

        content_data: Dict[str, Any] = dict()

        if album_messages:
            content_data = content_service.extract_media_content(
                messages=album_messages
            )
        else:
            content_data = content_service.extract_media_content(messages=[message])

        content_data.update(state_data)  # Объединяем со state_data

        await content_service.save_template(
            author_username=message.from_user.username,
            content=content_data,
        )
        await message.answer(f"✅ Шаблон '{title}' создан!")

    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка при создании шаблона: {str(e)}")
        await state.clear()
