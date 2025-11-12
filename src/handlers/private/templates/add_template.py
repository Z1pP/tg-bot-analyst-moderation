import logging
from typing import Any, Dict

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_inline_ikb
from keyboards.inline.templates import cancel_template_ikb, templates_menu_ikb
from middlewares import AlbumMiddleware
from services.categories import CategoryService
from services.templates import TemplateContentService
from states import TemplateStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

from .common import common_process_template_title_handler

router = Router(name=__name__)
router.message.middleware(AlbumMiddleware())
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "add_template",
    TemplateStateManager.templates_menu,
)
async def add_template_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик добавления нового шаблона"""
    await callback.answer()

    try:
        category_service: CategoryService = container.resolve(CategoryService)
        categories = await category_service.get_categories()

        if not categories:
            msg_text = "Чтобы создать шаблон, сначала создайте хотя бы одну категорию."
            await callback.message.edit_text(
                text=msg_text,
                reply_markup=templates_menu_ikb(),
            )
            return

        first_page_categories = categories[:CATEGORIES_PAGE_SIZE]

        await callback.message.edit_text(
            text="Пожалуйста, выберите категорию шаблона.",
            reply_markup=categories_inline_ikb(
                categories=first_page_categories,
                page=1,
                total_count=len(categories),
            ),
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.process_template_category,
        )

    except Exception as e:
        logger.error(f"Ошибка при начале создания шаблона: {e}")
        await callback.message.edit_text(
            text="Произошла ошибка при создании шаблона.",
            reply_markup=templates_menu_ikb(),
        )


@router.callback_query(
    F.data.startswith("category__"),
    TemplateStateManager.process_template_category,
)
async def process_template_category_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    """Обработчик выбора категории шаблона"""
    await callback.answer()

    try:
        category_id = int(callback.data.split("__")[1])
    except (IndexError, ValueError):
        logger.warning("Некорректный формат callback_data: %s", callback.data)
        return await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ Некорректный запрос. Повторите действие через меню.",
            reply_markup=templates_menu_ikb(),
        )

    await state.update_data(
        category_id=category_id, active_message_id=callback.message.message_id
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Отправьте название шаблона:",
        reply_markup=cancel_template_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.process_template_title,
    )


@router.message(TemplateStateManager.process_template_title)
async def process_template_title_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    """Обработчик получения названия нового шаблона"""
    await common_process_template_title_handler(
        message=message,
        state=state,
        bot=bot,
    )


@router.message(TemplateStateManager.process_template_content)
async def process_template_content_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    album_messages: list[Message] | None = None,
):
    """Обработчик получения контента шаблона"""
    state_data = await state.get_data()
    title = state_data.get("title")
    active_message_id = state_data.get("active_message_id")

    try:
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

        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"✅ Шаблон '{title}' создан!",
                reply_markup=templates_menu_ikb(),
            )

    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {e}", exc_info=True)
        await safe_edit_message(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text="❌ Ошибка при создании шаблона",
            reply_markup=templates_menu_ikb(),
        )

    await log_and_set_state(
        message=message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )
