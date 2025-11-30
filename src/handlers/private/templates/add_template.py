import logging
from typing import Any, Dict

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_select_only_ikb
from keyboards.inline.templates import cancel_template_ikb, templates_menu_ikb
from middlewares import AlbumMiddleware
from services.categories import CategoryService
from services.templates import TemplateContentService
from states import TemplateStateManager
from usecases.categories import GetCategoriesPaginatedUseCase
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
            msg_text = Dialog.Template.CREATE_CATEGORY_FIRST
            await callback.message.edit_text(
                text=msg_text,
                reply_markup=templates_menu_ikb(),
            )
            return

        first_page_categories = categories[:CATEGORIES_PAGE_SIZE]

        await callback.message.edit_text(
            text=Dialog.Template.SELECT_CATEGORY,
            reply_markup=categories_select_only_ikb(
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
            text=Dialog.Template.ERROR_CREATE_TEMPLATE,
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
            text=Dialog.Template.INVALID_REQUEST,
            reply_markup=templates_menu_ikb(),
        )

    await state.update_data(
        category_id=category_id, active_message_id=callback.message.message_id
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Template.SEND_TEMPLATE_NAME,
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
                text=Dialog.Template.TEMPLATE_CREATED.format(title=title),
                reply_markup=templates_menu_ikb(),
            )

    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {e}", exc_info=True)
        await safe_edit_message(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Template.ERROR_CREATE_TEMPLATE_FAILED,
            reply_markup=templates_menu_ikb(),
        )

    await log_and_set_state(
        message=message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )


@router.callback_query(
    F.data.startswith("prev_categories_page__"),
    TemplateStateManager.process_template_category,
)
async def prev_categories_page_for_template_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на предыдущую страницу категорий при добавлении шаблона"""
    await callback.answer()

    try:
        current_page = int(callback.data.split("__")[1])
        prev_page = max(1, current_page - 1)

        usecase: GetCategoriesPaginatedUseCase = container.resolve(
            GetCategoriesPaginatedUseCase
        )
        offset = (prev_page - 1) * CATEGORIES_PAGE_SIZE
        categories, total_count = await usecase.execute(
            limit=CATEGORIES_PAGE_SIZE, offset=offset
        )

        keyboard = categories_select_only_ikb(
            categories=categories,
            page=prev_page,
            total_count=total_count,
        )

        await callback.message.edit_reply_markup(reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при переходе на предыдущую страницу категорий: {e}")
        await callback.answer(Dialog.Template.ERROR_PREV_PAGE)


@router.callback_query(
    F.data.startswith("next_categories_page__"),
    TemplateStateManager.process_template_category,
)
async def next_categories_page_for_template_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик перехода на следующую страницу категорий при добавлении шаблона"""
    await callback.answer()

    try:
        current_page = int(callback.data.split("__")[1])
        next_page = current_page + 1

        usecase: GetCategoriesPaginatedUseCase = container.resolve(
            GetCategoriesPaginatedUseCase
        )
        offset = (next_page - 1) * CATEGORIES_PAGE_SIZE
        categories, total_count = await usecase.execute(
            limit=CATEGORIES_PAGE_SIZE, offset=offset
        )

        if not categories:
            await callback.answer(Dialog.Template.NO_MORE_CATEGORIES)
            return

        keyboard = categories_select_only_ikb(
            categories=categories,
            page=next_page,
            total_count=total_count,
        )

        await callback.message.edit_reply_markup(reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при переходе на следующую страницу категорий: {e}")
        await callback.answer(Dialog.Template.ERROR_NEXT_PAGE)


@router.callback_query(
    TemplateStateManager.process_template_chat,
    F.data.startswith(CallbackData.Chat.PREFIX_TEMPLATE_SCOPE),
)
async def process_template_chat_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_TEMPLATE_SCOPE, ""))

    if chat_id == -1:
        await state.update_data(chat_id=None)
    else:
        await state.update_data(chat_id=int(chat_id))

    text = Dialog.Chat.ENTER_TEMPLATE_NAME

    await callback.message.answer(text=text)

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.process_template_title,
    )
