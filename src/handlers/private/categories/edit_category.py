import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from container import container
from usecases.categories import UpdateCategoryNameUseCase
from states import TemplateStateManager
from utils.exception_handler import handle_exception

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(TemplateStateManager.editing_category_name)
async def process_edit_category_name(message: Message, state: FSMContext) -> None:
    """Обработчик изменения названия категории"""
    try:
        data = await state.get_data()
        category_id = data.get("edit_category_id")

        if not category_id:
            await message.answer("❌ Ошибка: категория не найдена")
            await state.clear()
            return

        new_name = message.text.strip()

        # Обновляем название через Use Case
        usecase: UpdateCategoryNameUseCase = container.resolve(UpdateCategoryNameUseCase)
        success = await usecase.execute(category_id, new_name)

        if success:
            await message.answer(
                f"✅ Название категории изменено на: <b>{new_name}</b>"
            )
        else:
            await message.answer("❌ Ошибка при обновлении названия категории")

        await state.set_state(TemplateStateManager.templates_menu)
        await state.update_data(edit_category_id=None, original_category_name=None)

    except Exception as e:
        await handle_exception(message, e, "process_edit_category_name")
        await state.clear()
