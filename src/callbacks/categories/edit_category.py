import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from repositories import TemplateCategoryRepository
from states import TemplateStateManager
from utils.exception_handler import handle_exception

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_category__"))
async def edit_category_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования категории"""
    try:
        category_id = int(query.data.split("__")[1])

        # Получаем категорию из БД
        category_repo: TemplateCategoryRepository = container.resolve(
            TemplateCategoryRepository
        )
        category = await category_repo.get_category_by_id(category_id)

        if not category:
            await query.answer("Категория не найдена", show_alert=True)
            return

        # Сохраняем данные категории в state
        await state.update_data(
            edit_category_id=category_id, original_category_name=category.name
        )

        await state.set_state(TemplateStateManager.editing_category_name)

        await query.message.edit_text(
            text=f"<b>Редактирование категории:</b> {category.name}\n\n"
            "Введите новое название для категории:"
        )

        logger.info(
            f"Начато редактирование категории {category_id} пользователем {query.from_user.username}"
        )

    except Exception as e:
        await handle_exception(query.message, e, "edit_category_callback")
    finally:
        await query.answer()
