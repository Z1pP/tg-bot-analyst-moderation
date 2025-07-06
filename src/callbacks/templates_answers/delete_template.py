import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates_answers import conf_remove_template_kb
from repositories import MessageTemplateRepository
from states.response_state import QuickResponseStateManager

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith("remove_template__"),
    QuickResponseStateManager.listing_templates,
)
async def remove_template_callback(
    query: CallbackQuery,
    state: FSMContext,
):
    try:
        try:
            template_id = int(query.data.split("__")[1])
        except (IndexError, ValueError):
            logger.warning(f"Неверный template_id формат: {query.data}")
            await query.answer("❌ Неверный формат ID шаблона", show_alert=True)
            return

        logger.info(
            "Пользователь %s запросил удаление шаблона ID: %d",
            query.from_user.full_name,
            template_id,
        )

        await state.update_data(template_id=int(template_id))
        await state.set_state(QuickResponseStateManager.removing_template)

        await query.message.edit_text(
            text="Вы уверены, что хотите удалить шаблон?",
            reply_markup=conf_remove_template_kb(),
        )
    except Exception as e:
        logger.error(f"Ошибка в remove_template_callback: {e}", exc_info=True)
        await query.answer("⚠️ Произошла ошибка", show_alert=True)


@router.callback_query(
    F.data.startswith("conf_remove_template__"),
    QuickResponseStateManager.removing_template,
)
async def confirmation_removing_template(
    query: CallbackQuery,
    state: FSMContext,
):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        template_id = data.get("template_id")

        if not template_id:
            logger.error("Шаблон с ID=%d не найден", template_id)
            await query.answer("❌ Ошибка: ID шаблона не найден", show_alert=True)
            return

        # Парсим ответ пользователя
        answer = query.data.split("__")[1]

        if answer != "yes":
            await state.set_state(QuickResponseStateManager.templates_menu)
            await query.message.edit_text(
                text="❌ Удаление отменено",
            )
            return

        # Удаляем шаблон
        resp_repo: MessageTemplateRepository = container.resolve(
            MessageTemplateRepository
        )
        await resp_repo.delete_template(template_id=template_id)

        logger.info(f"Шаблон с ID={template_id} успешно удален")

        # Обновляем сообщение
        await query.message.edit_text(
            text="✅ Шаблон успешно удален", reply_markup=None
        )
        await state.set_state(QuickResponseStateManager.templates_menu)

    except Exception as e:
        logger.error(f"Ошибка при удалении шаблона: {str(e)}", exc_info=True)
        await query.answer("⚠️ Произошла ошибка при удалении", show_alert=True)
