import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from exceptions.category import CategoryNotFoundError
from keyboards.inline.categories import categories_inline_ikb, conf_remove_category_kb
from keyboards.inline.templates import templates_menu_ikb
from services.categories import CategoryService
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import DeleteCategoryUseCase, GetCategoryByIdUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith("remove_category__"),
    TemplateStateManager.listing_categories,
)
async def remove_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик запроса на удаление категории"""
    await callback.answer()

    try:
        category_id = int(callback.data.split("__")[1])
    except (IndexError, ValueError):
        logger.warning("Некорректный формат callback_data: %s", callback.data)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ Некорректный запрос. Повторите действие через меню.",
            reply_markup=templates_menu_ikb(),
        )
        return

    logger.info(
        "Пользователь '%s' инициировал удаление категории ID=%d",
        callback.from_user.full_name,
        category_id,
    )

    await state.update_data(category_id=category_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Вы уверены, что хотите удалить эту категорию?",
        reply_markup=conf_remove_category_kb(),
    )

    await state.set_state(CategoryStateManager.removing_category)


@router.callback_query(
    F.data == "conf_remove_category",
    CategoryStateManager.removing_category,
)
async def confirm_removing_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик подтверждения удаления категории"""
    await callback.answer()

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        logger.warning("Попытка удалить категорию без сохранённого ID в состоянии")
        return await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ Не удалось определить категорию для удаления.",
            reply_markup=templates_menu_ikb(),
        )

    try:
        usecase: DeleteCategoryUseCase = container.resolve(DeleteCategoryUseCase)
        category = await usecase.execute(
            category_id=category_id, admin_tg_id=str(callback.from_user.id)
        )
        category_name = category.name
        text = f"✅ Категория <b>{category_name}</b> успешно удалена."
        logger.info("Категория ID=%d успешно удалена", category_id)

        # Получаем список категорий для отображения
        category_service: CategoryService = container.resolve(CategoryService)
        categories = await category_service.get_categories()

        if not categories:
            # Если категорий не осталось, возвращаемся в меню
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"{text}\n\n❗ Категорий не осталось.",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        first_page_categories = categories[:CATEGORIES_PAGE_SIZE]

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{text}\n\nВыберите категорию:",
            reply_markup=categories_inline_ikb(
                categories=first_page_categories,
                page=1,
                total_count=len(categories),
            ),
        )

        await state.set_state(TemplateStateManager.listing_categories)

    except CategoryNotFoundError as e:
        logger.warning("Категория ID=%d не найдена: %s", category_id, e)
        text = e.get_user_message()
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=templates_menu_ikb(),
        )
        await state.set_state(TemplateStateManager.templates_menu)

    except Exception:
        logger.exception("Ошибка при удалении категории ID=%d", category_id)
        text = "⚠️ Произошла ошибка при удалении категории."
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=templates_menu_ikb(),
        )
        await state.set_state(TemplateStateManager.templates_menu)


@router.callback_query(
    F.data == "cancel_remove_category",
    CategoryStateManager.removing_category,
)
async def cancel_removing_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик отмены удаления категории"""
    await callback.answer()

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        logger.warning(
            "Попытка отменить удаление категории без сохранённого ID в состоянии"
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Удаление категории отменено.",
            reply_markup=templates_menu_ikb(),
        )
        await state.set_state(TemplateStateManager.templates_menu)
        return

    try:
        # Получаем название категории
        get_category_usecase: GetCategoryByIdUseCase = container.resolve(
            GetCategoryByIdUseCase
        )
        category = await get_category_usecase.execute(category_id)
        category_name = category.name if category else "неизвестная"

        logger.info(
            "Пользователь '%s' отменил удаление категории '%s'",
            callback.from_user.full_name,
            category_name,
        )

        # Получаем список категорий для отображения
        category_service: CategoryService = container.resolve(CategoryService)
        categories = await category_service.get_categories()

        if not categories:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"❌ Удаление категории {category_name} отменено.\n\n❗ Категорий не найдено.",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        first_page_categories = categories[:CATEGORIES_PAGE_SIZE]

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"❌ Удаление категории {category_name} отменено.\n\nВыберите категорию:",
            reply_markup=categories_inline_ikb(
                categories=first_page_categories,
                page=1,
                total_count=len(categories),
            ),
        )

        await state.set_state(TemplateStateManager.listing_categories)

    except Exception as e:
        logger.exception("Ошибка при отмене удаления категории: %s", e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Удаление категории отменено.",
            reply_markup=templates_menu_ikb(),
        )
        await state.set_state(TemplateStateManager.templates_menu)
