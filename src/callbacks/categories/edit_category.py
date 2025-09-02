import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from states import TemplateStateManager
from usecases.categories import GetCategoryByIdUseCase
from utils.exception_handler import handle_exception

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_category__"))
async def edit_category_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования категории"""
    try:
        category_id = int(query.data.split("__")[1])

        # Получаем категорию через Use Case
        usecase: GetCategoryByIdUseCase = container.resolve(GetCategoryByIdUseCase)
        category_dto = await usecase.execute(category_id)

        if not category_dto:
            await query.answer("Категория не найдена", show_alert=True)
            return

        # Сохраняем данные категории в state
        await state.update_data(
            edit_category_id=category_id, original_category_name=category_dto.name
        )

        await state.set_state(TemplateStateManager.editing_category_name)

        await query.message.edit_text(
            text=f"<b>Редактирование категории:</b> {category_dto.name}\n\n"
            "Введите новое название для категории:"
        )

        logger.info(
            f"Начато редактирование категории {category_id} пользователем {query.from_user.username}"
        )

    except Exception as e:
        await handle_exception(query.message, e, "edit_category_callback")
    finally:
        await query.answer()
