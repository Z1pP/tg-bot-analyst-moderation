import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.categories import conf_remove_category_kb
from usecases.categories import DeleteCategoryUseCase
from states import TemplateStateManager

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith("remove_category__"),
    TemplateStateManager.listing_categories,
)
async def remove_category_callback(
    query: CallbackQuery,
    state: FSMContext,
):
    try:
        try:
            category_id = int(query.data.split("__")[1])
        except (IndexError, ValueError):
            logger.warning(f"Неверный category_id формат: {query.data}")
            await query.answer("❌ Неверный формат ID категории", show_alert=True)
            return

        logger.info(
            "Пользователь %s запросил удаление категории ID: %d",
            query.from_user.full_name,
            category_id,
        )

        await state.update_data(category_id=int(category_id))
        await state.set_state(TemplateStateManager.removing_category)

        await query.message.edit_text(
            text="Вы уверены, что хотите удалить эту категорию?",
            reply_markup=conf_remove_category_kb(),
        )
    except Exception as e:
        logger.error(f"Ошибка в remove_category_callback: {e}", exc_info=True)
        await query.answer("⚠️ Произошла ошибка", show_alert=True)


@router.callback_query(
    F.data.startswith("conf_remove_category__"),
    TemplateStateManager.removing_category,
)
async def confirmation_removing_category(
    query: CallbackQuery,
    state: FSMContext,
):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        category_id = data.get("category_id")

        if not category_id:
            logger.error("Категория с ID=%d не найден", category_id)
            await query.answer("❌ Ошибка: ID категории не найден", show_alert=True)
            return

        # Парсим ответ пользователя
        answer = query.data.split("__")[1]

        if answer != "yes":
            await state.set_state(TemplateStateManager.templates_menu)
            await query.message.edit_text(
                text="❌ Удаление отменено",
            )
            return

        # Удаляем категорию через Use Case
        usecase: DeleteCategoryUseCase = container.resolve(DeleteCategoryUseCase)
        await usecase.execute(category_id=category_id)

        # Обновляем сообщение
        await query.message.edit_text(
            text="✅ Категория успешно удалена", reply_markup=None
        )
        await state.set_state(TemplateStateManager.templates_menu)

    except Exception as e:
        logger.error(f"Ошибка при удалении категории: {str(e)}", exc_info=True)
        await query.answer("⚠️ Произошла ошибка при удалении", show_alert=True)
